from typing import Any
from pathlib import Path

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
    require_language,
    select_by_language,
)
from connectors import athena



class CustomAPIOperation(EndpointHandlerTemplate):

    connector = athena
    query_path = Path(__file__).with_name("query.sql")

    
    def bind_parameters(self) -> list:
        
        body = self.body

        # validate request payload
        language = body.get("language")
        require_language(language)

        from_booking_dttm = body.get("fromBookingDateTime") # where data dt no datetime
        to_booking_dttm = body.get("toBookingDateTime")
        account_id = body.get("accountId")
        account_sub_type = body.get("accountSubType")

        return [account_id]
    

    def build_mapping(self, query_result: Any):

        aux_ref_id = self.body.get("auxiliaryReferenceId")
        account_id = self.body.get("accountId")
        language = self.body.get("language")

        transaction_entries = [
            {
                "bookingDateTime": row.get("bookingDateTime"),                                       # 1.3.1
                "valueDateTime": row.get("valueDateTime"),                                           # 1.3.2
                "subAccountLevelMaturityDate": row.get("subAccountLevelMaturityDate"),               # 1.3.3
                "commonTransactionCode": {                                                           # 1.3.4
                    "domainCode": row.get("domainCode"),                                             # 1.3.4.1
                    "familyCode": row.get("familyCode"),                                             # 1.3.4.2
                    "subFamilyCode": row.get("subFamilyCode"),                                       # 1.3.4.3
                },
                "proprietaryBankTransactionCode": row.get("proprietaryBankTransactionCode"),         # 1.3.5
                "proprietaryBankTransactionDescription": row.get("proprietaryBankTransactionDescription"),  # 1.3.6
                "creditDebitIndicator": row.get("creditDebitIndicator"),                             # 1.3.7
                "amount": row.get("amount"),                                                         # 1.3.8
                "amountCurrency": row.get("amountCurrency"),                                         # 1.3.9
                "transactionId": row.get("transactionId"),                                           # 1.3.10
                "transactionRef": row.get("transactionRef"),                                         # 1.3.11
                "transactionInformation": row.get("transactionInformation"),                         # 1.3.12
                "creditorAccountId": row.get("creditorAccountId"),                                   # 1.3.13
                "creditorAccountName": row.get("creditorAccountName"),                               # 1.3.14
                "receivingInstitutionCode": row.get("receivingInstitutionCode"),                     # 1.3.15
                "receivingInstitutionName": row.get("receivingInstitutionName"),                     # 1.3.16
                "deptorAccountId": row.get("debtorAccountId"),                                       # 1.3.17 (spec spelling)
                "debtorAccountName": row.get("debtorAccountName"),                                   # 1.3.18
                "sendingInstitutionCode": row.get("sendingInstitutionCode"),                         # 1.3.19
                "sendingInstitutionName": row.get("sendingInstitutionName"),                         # 1.3.20
                "merchantName": select_by_language(                                                  # 1.3.21
                    language=language,
                    th_value=row.get("merchantName"),
                    en_value=row.get("merchantNameEn"),
                ),
            }

            for row in query_result
        ]

        return {
            "TransactionHeader": {                                                                   # 1
                "auxiliaryReferenceId": aux_ref_id,                                                  # 1.1
                "accountId": account_id,                                                             # 1.2
                "TransactionEntries": transaction_entries,                                           # 1.3
            }
        }



OPERATION_CLASS = CustomAPIOperation
