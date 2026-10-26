from typing import Any

from endpoint_handler_template import EndpointHandlerTemplate



class CustomAPIOperation(EndpointHandlerTemplate):

    def bind_parameters(self) -> list:
            
        body = self.response.get("body")

        from_booking_dttm = body.get("fromBookingDateTime")
        to_booking_dttm = body.get("toBookingDateTime")
        language = body.get("Language")
        aux_ref_id = body.get("auxiliaryReferenceId")

        identifier = body.get("identifier")

        account_id = body.get("accountId")
        account_sub_type = body.get("accountSubType")

        return [
            from_booking_dttm,
            to_booking_dttm,
            language, 
            aux_ref_id, 
            identifier, 
            account_id, 
            account_sub_type
        ]
    
    

    def build_mapping(self, query_result: Any):
            
        body = self.response.get("body")

        auxiliary_ref_id = self.body.get("auxiliaryReferenceId")

        return {
                "StatementHeader": {
                    "creationDateTime": "",
                    "statementId": "",
                    "auxiliaryReferenceId": "",
                    "institutionName": "",
                    "accountId": "",

                    "ownerType": "",
                    "accountType": "",
                    "accountSubType": "",
                    "accountStatus": "",
                    "accountName": "",

                    "accountOwner": "",
                    "openingDate": "",
                    "accountLevelMaturityDate": "",
                    "lastLedgerBalanceAmount": "",
                    "lastLedgerBalanceCurrency": "",

                    "lastAvaliableBalanceAmount": "",
                    "lastAvailableBalanceCurrency": "",
                    "startDateTime": "",
                    "endDateTime": "",
                    "numberofTotalItems": "",

                    "statementDescription": "",
                    "creditLimit": "",
                    "homeBranch": "",
                

                },

                "statementEntries": {
                    "bookingDateTime": "",
                    "valueDateTime": "",
                    "subAccountLevelMaturityDate": "",
                    "commonTransactionCode": "", # struct(domainCode, familyCode, subFamilyCode, )
                    "proprietaryBankTransactionCode": "",

                    "proprietaryBankTransactionDescription": "",
                    "Type": "",
                    "accountSubType": "",
                    "accountStatus": "",
                    "accountName": "",

                    "accountOwner": "",
                    "openingDate": "",
                    "accountLevelMaturityDate": "",
                    "lastLedgerBalanceAmount": "",
                    "lastLedgerBalanceCurrency": "",

                    "lastAvaliableBalanceAmount": "",
                    "lastAvailableBalanceCurrency": "",
                    "startDateTime": "",
                    "endDateTime": "",
                    "numberofTotalItems": "",

                    "lastAvaliableBalanceAmount": "",
                    "lastAvailableBalanceCurrency": "",
                    "startDateTime": "",
                    "endDateTime": "",
                    "numberofTotalItems": "",

                    "statementDescription": "",
                    "creditLimit": "",
                    "homeBranch": "",
                }
        }



OPERATION_CLASS = CustomAPIOperation
