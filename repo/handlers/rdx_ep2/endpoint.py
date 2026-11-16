from typing import Any
from pathlib import Path

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
    require_subtype,
    single_row,
    select_by_language,
    require_language,
    MART_SUBTYPES,
    to_api_subtype,
    fill_null,
)
from connectors import dynamo


class CustomAPIOperation(EndpointHandlerTemplate):

    connector = dynamo
    query_path = Path(__file__).with_name("query.sql")
    REQUIRED_FIELDS = ("auxiliaryReferenceId", "accountId", "accountSubType")

    
    def bind_parameters(self) -> dict:

        body = self.body

        account_id = body.get("accountId")
        account_sub_type = body.get("accountSubType")
        language = body.get("language")

        require_language(language)
        require_subtype(account_sub_type)

        return {
            "account_id": account_id,
            "mart_account_sub_type": MART_SUBTYPES[account_sub_type],
        }


    def build_mapping(self, rows: Any):
        
        body = self.body
        row = single_row(rows)
        
        aux_ref_id = body.get("auxiliaryReferenceId")
        language = body.get("language")
        
        return {
            "auxiliaryReferenceId": aux_ref_id,
            "institutionName": fill_null(row.get("institutionName")),
            "accountId": fill_null(row.get("accountId")),
            "ownerType": fill_null(row.get("ownerType")),
            "productAccountType": fill_null(row.get("accountType")),
            "accountSubType": fill_null(to_api_subtype(row.get("accountSubType"))),
            "accountStatus": fill_null(row.get("accountStatus")),
            "accountName": fill_null(select_by_language(
                language=language,
                th_value=row.get("accountName"),
                en_value=row.get("accountNameEn"),
            )),
            "accountOwner": fill_null(row.get("accountOwner")),
            "openingDate": fill_null(row.get("openingDate"), kind="timestamp"),
            "homeBranch": fill_null(select_by_language(
                            language=language,
                            th_value=row.get("homeBranch"),
                            en_value=row.get("homeBranchEn"),
                        )),
        }



OPERATION_CLASS = CustomAPIOperation
