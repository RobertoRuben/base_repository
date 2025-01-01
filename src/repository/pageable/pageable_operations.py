from sqlalchemy import BinaryExpression, or_
from sqlmodel import SQLModel, Session, select, func
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from typing import Generic, List, Type, Optional, Literal, TypeVar
from natsort import natsorted
from src.repository.pageable.page import Page, PageInfo

# Generic type T bound to SQLModel
T = TypeVar("T", bound=SQLModel)

class PageableOperations(Generic[T]):
    """
    Pageable operations for database entities supporting pagination, sorting, and filtering.
    
    Attributes:
        model_class (Type[T]): The SQLModel class type for entities.
    
    Example:
        ```python
        class User(SQLModel):
            id: int
            name: str
            
        pageable = PageableOperations[User](User)
        page = pageable.get_page(session, page=1, size=10)
        ```
    """
    def __init__(self, model_class: Type[T]):
        """
        Initialize PageableOperations with a specific model class.
        
        :param model_class: The SQLModel class to operate on.
        """
        self.model_class = model_class

    def get_page(
        self,
        session: Session,
        page: int = 1,
        size: int = 10,
        join_relations: Optional[List[RelationshipProperty]] = None,
        join_type: Optional[Literal["inner", "left"]] = None,
        select_fields: Optional[List[InstrumentedAttribute]] = None,
        where: Optional[BinaryExpression] = None,
        order_by: Optional[str] = None,
        sort_order: Optional[Literal["asc", "desc"]] = None,
    ) -> Page[dict]:
        """
        Retrieve a paginated and optionally filtered/sorted list of records.

        :param session: The active SQLAlchemy session to execute the query.
        :param page: The current page number (1-based index).
        :param size: The number of items per page (maximum capped at 100).
        :param join_relations: A list of model relationships to join in the query.
        :param join_type: The type of SQL join ("inner" or "left"). Default is "inner".
        :param select_fields: A list of specific fields to include in the SELECT clause.
        :param where: A SQLAlchemy binary expression for filtering results.
        :param order_by: The name of the field to sort the results by.
        :param sort_order: The sorting order, either "asc" for ascending or "desc" for descending. Default is "asc".
        :return: A Page object containing paginated results and metadata.
        :raises ValueError: If invalid pagination parameters are provided.
        :raises SQLAlchemyError: For any database-related errors.
        """
        try:
            # Validate pagination boundaries
            if page < 1 or size < 1:
                raise ValueError("Page and size must be greater than 0.")

            join_type = join_type or "inner"
            sort_order = sort_order or "asc"

            # Build the base query
            query = select(*select_fields) if select_fields else select(self.model_class)

            # Add explicit joins for relationships
            if join_relations:
                for relation in join_relations:
                    if join_type == "inner":
                        query = query.join(relation)
                    elif join_type == "left":
                        query = query.outerjoin(relation)

            # Apply WHERE conditions
            if where is not None:
                query = query.where(where)

            # Count total items for pagination
            count_query = select(func.count()).select_from(self.model_class)
            if join_relations:
                for relation in join_relations:
                    if join_type == "inner":
                        count_query = count_query.join(relation)
                    elif join_type == "left":
                        count_query = count_query.outerjoin(relation)
            if where is not None:
                count_query = count_query.where(where)
            total_items = session.execute(count_query).scalar()

            # Execute the main query without sorting
            results = session.execute(query).all()

            # Transform query results into dictionaries
            items = [dict(row._mapping) for row in results]

            # Apply natural sorting if order_by is provided
            if order_by:
                items = natsorted(
                    items,
                    key=lambda x: x.get(order_by, ""),
                    reverse=(sort_order == "desc")
                )

            # Apply pagination to the sorted items
            start = (page - 1) * size
            end = start + size
            paginated_items = items[start:end]

            # Calculate total pages
            total_pages = (total_items + size - 1) // size if total_items > 0 else 1

            # Build and return the Page object
            page_info = PageInfo(
                current_page=page,
                page_size=size,
                total_items=total_items,
                total_pages=total_pages,
            )
            return Page(data=paginated_items, pagination=page_info)

        except ValueError as e:
            raise e  # Let ValueError propagate as it is meaningful for users.
        except exec.SQLAlchemyError as e:
            # Re-raise SQLAlchemy exceptions with additional context
            raise RuntimeError(f"Database error occurred: {e}") from e
        
    
    def find_page(
        self,
        session: Session,
        search_term: str,
        search_fields: List[str],
        page: int = 1,
        size: int = 10,
        join_relations: Optional[List[RelationshipProperty]] = None,
        join_type: Optional[Literal["inner", "left"]] = None,
        order_by: Optional[str] = None,
        sort_order: Optional[Literal["asc", "desc"]] = None,
    ) -> Page[dict]:
        """
        Search and paginate records containing the search term in specified fields.

        Args:
            session: Database session
            search_term: Term to search for
            search_fields: List of fields to search in
            page: Page number (1-based index)
            size: Number of items per page
            join_relations: List of relationships to join in the query
            join_type: Type of SQL join ("inner" or "left")
            order_by: Field to sort results by
            sort_order: Sort direction ("asc" or "desc")

        Returns:
            Page[dict]: Page object containing results and metadata

        Raises:
            ValueError: If search parameters are invalid
            SQLModelError: If a database error occurs
            RuntimeError: For other unexpected errors

        Example:
            results = repo.find_page(
                session,
                search_term="john",
                search_fields=["name", "email"],
                page=1,
                size=10
            )
        """
        try:
            if not search_term or not search_fields:
                raise ValueError("Search term and search fields are required")

            # Build search conditions
            search_conditions = []
            for field in search_fields:
                try:
                    column = getattr(self.model_class, field)
                    search_conditions.append(
                        column.ilike(f"%{search_term}%")
                    )
                except AttributeError:
                    continue

            if not search_conditions:
                raise ValueError("No valid search fields found")

            # Combine conditions with OR
            where_condition = or_(*search_conditions)

            # Use get_page with search conditions
            return self.get_page(
                session=session,
                page=page,
                size=size,
                join_relations=join_relations,
                join_type=join_type,
                where=where_condition,
                order_by=order_by,
                sort_order=sort_order
            )

        except ValueError as e:
            raise e
        except exec.SQLAlchemyError as e:
            raise RuntimeError(f"Database error occurred: {str(e)}") from e 
        except Exception as e:
            raise RuntimeError(f"Search error: {str(e)}") from e
