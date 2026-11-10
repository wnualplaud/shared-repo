SELECT

        TRIM(D.RDXSRC_CODE)                                        AS RDXSRC_CODE
    ,   TRIM(D.REP_CODE)                                        AS REP_CODE
    ,   D.RDXSRC_COLL_ID                                           AS RDXSRC_COLL_ID
    ,   D.COLL_NO                                               AS COLL_NO
    ,   D.RDXSRC_COLL_ITEM_ID                                      AS RDXSRC_COLL_ITEM_ID
    ,   D.COLL_SPC_NO                                           AS COLL_SPC_NO
    ,   D.CREATE_DATE                                           AS CREATE_DATE

    ,   I.RDXSRC_ID                                                AS JOB_RDXSRC_ID
    ,   I.SPC_SURPRISE_CHECK                                    AS SPC_SURPRISE_CHECK
    ,   TRIM(I.REQUEST_OFFICE_CODE)                             AS REQUEST_OFFICE_CODE

    ,   B.BR_NO                                                 AS BR_NO
    ,   B.RDXBANK_GRP_CODE                                          AS RDXBANK_GRP_CODE

    ,   TRIM(R.REP_CODE)                                        AS REP_REP_CODE

    ,   C.RDXSRC_COLL_ID                                           AS COLL_RDXSRC_COLL_ID
    ,   TRIM(CAST(C.CMS_COLL_ID AS STRING))                     AS CMS_COLL_ID

    ,   K.N_RDXCUST                                                 AS CARD_N_RDXCUST

    ,   CASE WHEN I.RDXSRC_CODE IS NULL     THEN '1 no job row'
             WHEN B.BR_NO IS NULL        THEN '2 branch not RDXUNIT'
             WHEN R.REP_CODE IS NULL     THEN '3 no report row'
             WHEN C.RDXSRC_COLL_ID IS NULL  THEN '4 no collateral row'
             WHEN C.CMS_COLL_ID IS NULL  THEN '5 collateral without CMS id'
             WHEN K.N_RDXCUST IS NULL        THEN '6 no card row'
             ELSE                             '7 reaches the output'
        END                                                     AS STAGE

    ,   D.DL_DATA_DT                                            AS DL_DATA_DT
    ,   CURRENT_TIMESTAMP()                                     AS DL_LOAD_TS

FROM `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_REP_COLL_SPC_DETAIL D

    LEFT JOIN `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_INFO I
        ON TRIM(D.RDXSRC_CODE) = TRIM(I.RDXSRC_CODE)
       AND I.DL_DATA_DT = '${hivevar:dl_data_dt}'

    LEFT JOIN `RDXDW${hivevar:dbdwenv}`.RDX_DIM1 B
        ON TRIM(I.REQUEST_OFFICE_CODE) = B.BR_NO
       AND B.RDXBANK_GRP_CODE IN (
                'RDX_GRP1',
                'RDX_GRP2',
                'RDX_GRP3',
                'RDX_GRP4',
                'RDX_GRP5',
                'RDX_GRP6'
           )

    LEFT JOIN `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_REP_INFO R
        ON I.RDXSRC_ID = R.RDXSRC_ID
       AND TRIM(I.RDXSRC_CODE) = TRIM(R.RDXSRC_CODE)
       AND TRIM(D.REP_CODE) = TRIM(R.REP_CODE)
       AND R.DL_DATA_DT = '${hivevar:dl_data_dt}'

    LEFT JOIN `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_COLL C
        ON TRIM(D.RDXSRC_CODE) = TRIM(C.RDXSRC_CODE)
       AND D.RDXSRC_COLL_ID = C.RDXSRC_COLL_ID
       AND D.COLL_NO = C.COLL_NO
       AND C.DL_DATA_DT = '${hivevar:dl_data_dt}'

    LEFT JOIN (
        SELECT RDXSRC_CODE, CMS_COLL_ID, COUNT(*) AS N_RDXCUST
        FROM `${hivevar:tmp_db}`.`${hivevar:prefix}CARD`
        GROUP BY RDXSRC_CODE, CMS_COLL_ID
    ) K
        ON TRIM(D.RDXSRC_CODE) = K.RDXSRC_CODE
       AND TRIM(CAST(C.CMS_COLL_ID AS STRING)) = K.CMS_COLL_ID

WHERE D.DL_DATA_DT = '${hivevar:dl_data_dt}'

  AND D.COLL_TYPE_ID = 7
  AND D.COLL_SUBTYPE_ID = 1
  AND SUBSTR(CAST(D.CREATE_DATE AS STRING), 1, 10)
      BETWEEN '${hivevar:from_dt}' AND '${hivevar:to_dt}'
