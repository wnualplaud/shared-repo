from typing import Any
from pathlib import Path

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
    single_row,
    select_by_language,
    require_language,
)
from connectors import dynamo


class CustomAPIOperation(EndpointHandlerTemplate):

    connector = dynamo
    query_path = Path(__file__).with_name("query.sql")

    
    def bind_parameters(self) -> list:

        body = self.body

        # validate request payload
        language = body.get("language")
        require_language(language)


        account_id = body.get("accountId")
        account_sub_type = body.get("accountSubType")

        return [account_id, account_sub_type]
    

    def build_mapping(self, rows: Any):
        
        body = self.body
        row = single_row(rows)
        
        aux_ref_id = self.body.get("auxiliaryReferenceId")
        language = self.body.get("language")
        
        return {
            "auxiliaryReferenceId": aux_ref_id,
            "InstitutionName": row.get("institutionName", ""),
            "accountId": row.get("accountId", ""),
            "ownerType": row.get("ownerType", ""),
            "accountType": row.get("accountType", ""),
            "accountSubType": row.get("accountSubType", ""),
            "accountStatus": row.get("accountStatus", ""),
            "accountName": select_by_language(
                language=language,
                th_value=row.get("accountName"),
                en_value=row.get("accountNameEn"),
            ),
            "accountOwner": row.get("accountOwner", ""),
            "openingDate": row.get("openingDate", ""),
            "homeBranch": select_by_language(
                            language=language,
                            th_value=row.get("homeBranch"),
                            en_value=row.get("homeBranchEn"),
                        ),
        }



OPERATION_CLASS = CustomAPIOperation
