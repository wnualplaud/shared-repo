SELECT

        RDXSRC_INFO.RDXSRC_ID                                         AS RDXSRC_ID
    ,   TRIM(RDXSRC_INFO.RDXSRC_CODE)                                 AS RDXSRC_CODE
    ,   TRIM(RDXSRC_INFO.REQUEST_OFFICE_CODE)                      AS REQUEST_OFFICE_CODE
    ,   RDXSRC_INFO.SPC_SURPRISE_CHECK                             AS SPC_SURPRISE_CHECK
    ,   RDX_DIM.RDXBANK_GRP_CODE                                     AS RDXBANK_GRP_CODE

    ,   TRIM(RDXSRC_REP_INFO.REP_CODE)                             AS REP_CODE
    ,   RDXSRC_REP_INFO.OS_SURVEYER_NAME                           AS OS_SURVEYER_NAME
    ,   RDXSRC_REP_INFO.SURVEY_DATE                                AS SURVEY_DATE

    ,   RDXSRC_COLL.RDXSRC_COLL_ID                                    AS RDXSRC_COLL_ID
    ,   RDXSRC_COLL.COLL_NO                                        AS COLL_NO
    ,   TRIM(CAST(RDXSRC_COLL.CMS_COLL_ID AS STRING))              AS CMS_COLL_ID

    ,   COLL_SPC_DETAIL.RDXSRC_COLL_ITEM_ID                        AS RDXSRC_COLL_ITEM_ID
    ,   COLL_SPC_DETAIL.COLL_SPC_NO                             AS COLL_SPC_NO
    ,   COLL_SPC_DETAIL.PRODUCT_DESC                            AS PRODUCT_DESC
    ,   COLL_SPC_DETAIL.TOTAL_AMOUNT                            AS TOTAL_AMOUNT
    ,   COLL_SPC_DETAIL.UNIT_AMOUNT                             AS UNIT_AMOUNT
    ,   COLL_SPC_DETAIL.UNIT_PRICE                              AS UNIT_PRICE
    ,   COLL_SPC_DETAIL.CREATE_DATE                             AS CREATE_DATE

    ,   COLL_SPC_DETAIL.DL_DATA_DT                              AS DL_DATA_DT
    ,   CURRENT_TIMESTAMP()                                     AS DL_LOAD_TS

FROM `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_INFO RDXSRC_INFO

    INNER JOIN `RDXDW${hivevar:dbdwenv}`.RDX_DIM1 RDX_DIM
        ON TRIM(RDXSRC_INFO.REQUEST_OFFICE_CODE) = RDX_DIM.BR_NO
       AND RDX_DIM.RDXBANK_GRP_CODE IN (
                'RDX_GRP1',
                'RDX_GRP2',
                'RDX_GRP3',
                'RDX_GRP4',
                'RDX_GRP5',
                'RDX_GRP6'
           )

    INNER JOIN `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_REP_INFO RDXSRC_REP_INFO
        ON RDXSRC_INFO.RDXSRC_ID = RDXSRC_REP_INFO.RDXSRC_ID
       AND TRIM(RDXSRC_INFO.RDXSRC_CODE) = TRIM(RDXSRC_REP_INFO.RDXSRC_CODE)
       AND RDXSRC_REP_INFO.DL_DATA_DT = '${hivevar:dl_data_dt}'

    INNER JOIN `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_COLL RDXSRC_COLL
        ON TRIM(RDXSRC_INFO.RDXSRC_CODE) = TRIM(RDXSRC_COLL.RDXSRC_CODE)
       AND RDXSRC_COLL.DL_DATA_DT = '${hivevar:dl_data_dt}'
       AND RDXSRC_COLL.CMS_COLL_ID IS NOT NULL

    INNER JOIN `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_REP_COLL_SPC_DETAIL COLL_SPC_DETAIL
        ON TRIM(RDXSRC_INFO.RDXSRC_CODE) = TRIM(COLL_SPC_DETAIL.RDXSRC_CODE)
       AND TRIM(RDXSRC_REP_INFO.REP_CODE) = TRIM(COLL_SPC_DETAIL.REP_CODE)
       AND RDXSRC_COLL.RDXSRC_COLL_ID = COLL_SPC_DETAIL.RDXSRC_COLL_ID
       AND RDXSRC_COLL.COLL_NO = COLL_SPC_DETAIL.COLL_NO
       AND COLL_SPC_DETAIL.DL_DATA_DT = '${hivevar:dl_data_dt}'

WHERE RDXSRC_INFO.DL_DATA_DT = '${hivevar:dl_data_dt}'

  AND COLL_SPC_DETAIL.COLL_TYPE_ID = 7
  AND COLL_SPC_DETAIL.COLL_SUBTYPE_ID = 1
  AND SUBSTR(CAST(COLL_SPC_DETAIL.CREATE_DATE AS STRING), 1, 10)
      BETWEEN '${hivevar:from_dt}' AND '${hivevar:to_dt}'
