
class DetailDictMixin:
    default_detail: str
    default_code: str

    def __init__(self, detail=None, code=None) -> None:
        """
        Builds a detail dictionary for the error to give more information to API
        users.
        """
        detail_dict = {"detail": self.default_detail, "code": self.default_code}

        if isinstance(detail, dict):
            detail_dict.update(detail)
        elif detail is not None:
            detail_dict["detail"] = detail

        if code is not None:
            detail_dict["code"] = code

        super().__init__(detail_dict)
