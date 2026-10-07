select

        
        bookingDateTime 
    ,   valueDateTime
    ,   subAccountLevelMaturityDate
    ,   domainCode
    ,   familyCode
    ,   subFamilyCode
    ,   proprietaryBankTransactionCode
    ,   proprietaryBankTransactionDescription
    ,   creditDebitIndicator
    ,   amount
    ,   amountCurrency
    ,   transactionId
    ,   transactionRef
    ,   transactionInformation
    ,   creditorAccountId
    ,   creditorAccountName
    ,   receivingInstitutionCode
    ,   receivingInstitutionName
    ,   deptorAccountId
    ,   debtorAccountName
    ,   sendingInstitutionCode
    ,   sendingInstitutionName
    ,   merchantName

from rdx<env>_db1.rdx_tbl3
WHERE accountId = '<accountId>'
    AND accountSubType = '<accountSubType>'