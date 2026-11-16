
SELECT 

        accountId
    ,   lastLedgerBalanceAmount
    ,   lastLedgerBalanceCurrency
    ,   lastAvailableBalanceAmount
    ,   lastAvailableBalanceCurrency
    ,   creditLimit

FROM rdx${env}_tbl2
WHERE accountId = :account_id
    AND accountSubType IN(:mart_account_sub_type)
    AND ownerType = 'INDIVIDUAL'
    AND accountOwner = 'SINGLE'
    AND accountStatus = 'ACTIVE'

