from typing import Any
from pathlib import Path

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
    require_rows,
    require_subtype,
    select_by_language,
    require_language,
    MART_SUBTYPES, 
    to_api_subtype,
)
from connectors import dynamo



class CustomAPIOperation(EndpointHandlerTemplate):

    connector = dynamo
    query_path = Path(__file__).with_name("query.sql")
    query_all_path = Path(__file__).with_name("query_all.sql")

    def handle(self):
        account_sub_type = self.body.get("accountSubType")

        require_language(self.body.get("language"))
        if account_sub_type == "ALL":
            self.query_path = self.query_all_path
        else:
            require_subtype(account_sub_type)

        return super().handle()


    def bind_parameters(self) -> dict:

        body = self.body

        citizen_id = body.get("citizenId")
        account_sub_type = body.get("accountSubType")

        parameters = {"citizen_id": citizen_id, }
        if account_sub_type!="ALL":
            parameters["key_prefix"] = f"{MART_SUBTYPES[account_sub_type]}#"

        return parameters


    def build_mapping(self, rows: Any):

        aux_ref_id = self.body.get("auxiliaryReferenceId")
        language = self.body.get("language")

        account_list_entries = [
            {
                "institutionName": row.get("institutionName"),
                "identifier": "",
                "accountId": row.get("accountId"),
                "accountSubType": to_api_subtype(row.get("accountSubType")),
                "accountStatus": row.get("accountStatus"),
                "accountName": select_by_language(
                    language=language,
                    th_value=row.get("accountName"),
                    en_value=row.get("accountNameEn"),
                ),
            }

            for row in rows
        ]

        require_rows(account_list_entries, detail="No accounts found")

        return {
             "accountListHeader": {
                    "auxiliaryReferenceId": aux_ref_id,
                    "accountListEntries": account_list_entries
            }
        }



OPERATION_CLASS = CustomAPIOperation
