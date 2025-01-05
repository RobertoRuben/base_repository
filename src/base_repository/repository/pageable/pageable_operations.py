from sqlalchemy import BinaryExpression, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, Session, select, func
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from typing import Any, Dict, Generic, List, Type, Optional, Literal, TypeVar
from natsort import natsorted
from base_repository.repository.pageable.page import Page, PageInfo

T = TypeVar("T", bound=SQLModel)

class PageableOperations(Generic[T]):
    
    """Pagination operations with full IDE support and type checking.

    IDE Features:
        * Method autocompletion (type '.')
        * Parameter type hints (Ctrl+Space)
        * Return type inference (Page[T])
        * Go to definition support (F12)

    Available Methods:
        * get_page(...) -> Page[dict]
        * find_page(search_term, fields, ...) -> Page[dict]

    Example:
        ```python
        class UserRepo(PageableOperations[User]):
            def __init__(self, session: Session):
                super().__init__(User, session)

        # IDE Support Features:
        repo = UserRepo(session)
        page = repo.get_page(
            page=1,                    # Type hints
            size=10,                   # Type hints
            order_by="created_at",     # Field completion
            sort_order="desc"          # Value completion
        )

        # Search with pagination:
        results = repo.find_page(
            search_term="john",        # Type hints
            search_fields=["name"],    # Field suggestions
            page=1,
            size=10
        )

        # Access paginated data:
        for item in page.data:        # IDE shows dict keys
            print(item["name"])        # Field completion
        
        print(page.pagination.total_pages)  # PageInfo completion
        ```

    Type Support:
        * T = Your model type (SQLModel)
        * Page[dict] return type
        * Full parameter validation
        * Generic type checking
    """

    def __init__(self, model_class: Type[T], session: Session = None):
        """Initialize pagination operations with IDE support.

        IDE Features:
            * Type checking for model_class
            * Session validation hints
            * Field name completion
            * Go to definition support

        Args:
            model_class: SQLModel class for pagination
                    IDE shows available fields
            session: Database session for queries
                    IDE validates Session type

        Example:
            ```python
            class UserRepo(PageableOperations[User]):
                def __init__(self, session: Session):
                    super().__init__(User, session)  # IDE validates types
                    
            repo = UserRepo(session)
            # IDE shows available fields from User model
            ```

        Raises:
            ValueError: If model_class is not SQLModel type
        """
        if not issubclass(model_class, SQLModel):
            raise ValueError("model_class must be a SQLModel type")
        self.model_class = model_class
        self.session = session
        self.model_fields = list(self.model_class.__fields__.keys())

    def _validate_session(self):
        if not self.session:
            raise ValueError("Session not initialized")
        
    def _order_dict_by_model(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {field: item[field] for field in self.model_fields if field in item}

    def get_page(
        self,
        page: int = 1,
        size: int = 10,
        join_relations: Optional[List[RelationshipProperty]] = None,
        join_type: Optional[Literal["inner", "left"]] = None,
        select_fields: Optional[List[InstrumentedAttribute]] = None,
        where: Optional[BinaryExpression] = None,
        order_by: Optional[str] = None,
        sort_order: Optional[Literal["asc", "desc"]] = None,
    ) -> Page[dict]:
        """Get paginated results.

        Args:
            page: Page number (>= 1)
            size: Items per page (>= 1)
            join_relations: Related entities to join
            join_type: Join type ("inner" or "left")
            select_fields: Fields to select
            where: Filter condition
            order_by: Sort field name
            sort_order: Sort direction

        Returns:
            Page[dict]: Paginated results with metadata

        Example:
            ```python
            repo = UserRepository(session)
            page = repo.get_page(
                page=1,
                size=10,
                join_relations=[User.posts],  # Relation completion
                join_type="left",             # Value suggestion
                order_by="created_at",        # Field completion
                sort_order="desc"             # Value suggestion
            )
            
            for item in page.data:            # Type inference
                print(item["name"])           # Field completion
            
            print(page.pagination.total_pages) # PageInfo completion
            ```

        Raises:
            ValueError: If invalid page/size values
            RuntimeError: If database operation fails
        """
        self._validate_session()

        try:
            if page < 1 or size < 1:
                raise ValueError("Page and size must be greater than 0.")

            join_type = join_type or "inner"
            sort_order = sort_order or "asc"

            query = select(*select_fields) if select_fields else select(self.model_class)

            if join_relations:
                for relation in join_relations:
                    if join_type == "inner":
                        query = query.join(relation)
                    elif join_type == "left":
                        query = query.outerjoin(relation)

            if where is not None:
                query = query.where(where)

            count_query = select(func.count()).select_from(self.model_class)
            if join_relations:
                for relation in join_relations:
                    if join_type == "inner":
                        count_query = count_query.join(relation)
                    elif join_type == "left":
                        count_query = count_query.outerjoin(relation)
            if where is not None:
                count_query = count_query.where(where)
            total_items = self.session.execute(count_query).scalar()

            results = self.session.execute(query).all()

            items = []
            for row in results:
                item_dict = dict(row._mapping[self.model_class.__name__])
                ordered_item = self._order_dict_by_model(item_dict)
                items.append(ordered_item)

            if order_by:
                items = natsorted(
                    items,
                    key=lambda x: x.get(order_by, ""),
                    reverse=(sort_order == "desc")
                )

            start = (page - 1) * size
            end = start + size
            paginated_items = items[start:end]

            total_pages = (total_items + size - 1) // size if total_items > 0 else 1

            page_info = PageInfo(
                current_page=page,
                page_size=size,
                total_items=total_items,
                total_pages=total_pages,
            )
            return Page(data=paginated_items, pagination=page_info)

        except ValueError as e:
            raise e
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error occurred: {e}") from e

    def find_page(
        self,
        search_term: str,
        search_fields: List[str],
        page: int = 1,
        size: int = 10,
        join_relations: Optional[List[RelationshipProperty]] = None,
        join_type: Optional[Literal["inner", "left"]] = None,
        order_by: Optional[str] = None,
        sort_order: Optional[Literal["asc", "desc"]] = None,
    ) -> Page[dict]:
        """Search and paginate entities.

        Args:
            search_term: Text to search for
            search_fields: Fields to search in
            page: Page number (>= 1)
            size: Items per page (>= 1)
            join_relations: Related entities to join
            join_type: Join type ("inner" or "left")
            order_by: Sort field name
            sort_order: Sort direction

        Returns:
            Page[dict]: Paginated search results

        Example:
            ```python
            repo = UserRepository(session)
            # IDE shows parameter hints:
            results = repo.find_page(
                search_term="john",        # String validation
                search_fields=["name"],    # Field completion
                page=1,                    # Number validation
                size=10,                   # Number validation
                order_by="created_at",     # Field completion
                sort_order="desc"          # Value suggestion
            )
            
            for item in results.data:      # Type inference
                print(item["name"])        # Field completion
            
            total = results.pagination.total_items  # Property completion
            ```

        Raises:
            ValueError: If invalid search parameters
            RuntimeError: If database operation fails
        """
        self._validate_session()

        try:
            if not search_term or not search_fields:
                raise ValueError("Search term and search fields are required")

            search_conditions = []
            for field in search_fields:
                try:
                    column = getattr(self.model_class, field)
                    search_conditions.append(column.ilike(f"%{search_term}%"))
                except AttributeError:
                    continue

            if not search_conditions:
                raise ValueError("No valid search fields found")

            where_condition = or_(*search_conditions)

            return self.get_page(
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
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error occurred: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Search error: {str(e)}") from e
