from typing import Any
from pathlib import Path

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
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

        # aux_ref_id = body.get("auxiliaryReferenceId")
        citizen_id = body.get("citizen_id")
        account_sub_type = body.get("accountSubType")

        # return [language, aux_ref_id, citizen_id, account_sub_type]
        return [citizen_id, f"{account_sub_type}#"]
    

    def build_mapping(self, rows: Any):

        aux_ref_id = self.body.get("auxiliaryReferenceId")
        language = self.body.get("language")

        account_list_entries = [
            {
                "InstitutionName": row.get("institutionName"),
                "Identifier": "",
                "accountId": row.get("accountId"),
                "accountSubType": row.get("accountSubType"),
                "accountStatus": row.get("accountStatus"),
                "accountName": select_by_language(
                    language=language,
                    th_value=row.get("accountName"),
                    en_value=row.get("accountNameEn"),
                ),
            }

            for row in rows
        ]

        return {
             "accountListHeader": {
                    "auxiliaryReferenceId": aux_ref_id,
                    "accountListEntries": account_list_entries
            }
        }



OPERATION_CLASS = CustomAPIOperation
