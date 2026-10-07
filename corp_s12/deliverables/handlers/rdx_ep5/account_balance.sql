SELECT 
        InstitutionName
    ,   accountId
    ,   ownerType
    ,   accountType
    ,   accountSubType
    ,   accountStatus
    ,   CASE WHEN <language> = "EN" AND accountNameEn IS NOT NULL THEN
            THEN accountNameEn
            ELSE accountName
        END AS accountName
    ,   accountOwner
    ,   openingDate
    ,   CASE WHEN <language> = "EN" AND homeBranchEn IS NOT NULL THEN
            THEN homeBranchEn
            ELSE homeBranch
        END AS homeBranch

FROM rdx<env>_tbl2
WHERE accountId = <accountId>
    AND BEGIN_WITH(accountSubType, '#') = CONCAT('<resolvedAccountSubType>', '#')
