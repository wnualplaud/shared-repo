SELECT REASON, COUNT(*) AS N_PAIRS
FROM (
    SELECT CASE WHEN T_JOB.CODE IS NULL  THEN 'o0 only: job has no RDXSET set'
                WHEN T_COLL.CODE IS NULL THEN 'o0 only: set lacks the collateral'
                ELSE 'o0 only: card row not in the set' END AS REASON
    FROM (SELECT DISTINCT SRC_RDXSRC_COLL_ITEM_ID AS ID, RDXCUST_NO FROM `${hivevar:tmp_db}`.`${hivevar:prefix}OUT_O0`) O0
    LEFT JOIN (SELECT DISTINCT SRC_RDXSRC_COLL_ITEM_ID AS ID, RDXCUST_NO FROM `${hivevar:tmp_db}`.`${hivevar:prefix}OUT_OT1`) OT1
        ON O0.ID = OT1.ID AND O0.RDXCUST_NO = OT1.RDXCUST_NO
    INNER JOIN `${hivevar:tmp_db}`.`${hivevar:prefix}STOCK_ITEM` I
        ON O0.ID = I.RDXSRC_COLL_ITEM_ID
    LEFT JOIN (SELECT DISTINCT RDXSRCT_CODE AS CODE FROM `${hivevar:tmp_db}`.`${hivevar:prefix}RDXSET_T`) T_JOB
        ON I.RDXSRC_CODE = T_JOB.CODE
    LEFT JOIN (SELECT DISTINCT RDXSRCT_CODE AS CODE, COLL FROM `${hivevar:tmp_db}`.`${hivevar:prefix}RDXSET_T`) T_COLL
        ON I.RDXSRC_CODE = T_COLL.CODE AND I.CMS_COLL_ID = T_COLL.COLL
    WHERE OT1.ID IS NULL

    UNION ALL

    SELECT 'ot1 only' AS REASON
    FROM (SELECT DISTINCT SRC_RDXSRC_COLL_ITEM_ID AS ID, RDXCUST_NO FROM `${hivevar:tmp_db}`.`${hivevar:prefix}OUT_OT1`) OT1
    LEFT JOIN (SELECT DISTINCT SRC_RDXSRC_COLL_ITEM_ID AS ID, RDXCUST_NO FROM `${hivevar:tmp_db}`.`${hivevar:prefix}OUT_O0`) O0
        ON OT1.ID = O0.ID AND OT1.RDXCUST_NO = O0.RDXCUST_NO
    WHERE O0.ID IS NULL
) X
GROUP BY REASON
ORDER BY REASON;
