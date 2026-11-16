SELECT 
        institutionName
    ,   accountId
    ,   ownerType
    ,   accountType
    ,   accountSubType
    ,   accountStatus
    ,   accountName
    ,   accountNameEn
    ,   accountOwner
    ,   openingDate
    ,   homeBranch
    ,   homeBranchEn

FROM rdx${env}_tbl2
WHERE accountId = :account_id
    AND accountSubType IN(:mart_account_sub_type)
    AND ownerType = 'INDIVIDUAL'
    AND accountOwner = 'SINGLE'
    AND accountStatus = 'ACTIVE'
