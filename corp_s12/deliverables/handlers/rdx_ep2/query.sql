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

FROM rdx<env>_tbl2
WHERE accountId = ?
    AND accountSubType = ?
