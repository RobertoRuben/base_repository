from dataclasses import dataclass
from typing import List, Generic, TypeVar, Any, Dict

T = TypeVar("T")


@dataclass
class PageInfo:
    """
    Holds pagination-related data.

    Attributes:
        current_page (int): The current page number (1-indexed).
        page_size (int): The number of items per page.
        total_items (int): The total number of items matching the criteria.
        total_pages (int): The total number of pages available.
    """

    current_page: int
    page_size: int
    total_items: int
    total_pages: int


@dataclass
class Page(Generic[T]):
    """
    Represents a paginated set of results.

    Attributes:
        data (List[T]): The list of items for this page.
        pagination (PageInfo): Pagination metadata.
    """

    data: List[T]
    pagination: PageInfo

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Page object into a dictionary, useful for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary with 'data' and 'pagination' keys.
        """
        return {
            "data": self.data,
            "pagination": {
                "current_page": self.pagination.current_page,
                "page_size": self.pagination.page_size,
                "total_items": self.pagination.total_items,
                "total_pages": self.pagination.total_pages,
            },
        }
