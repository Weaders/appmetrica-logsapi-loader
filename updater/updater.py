#!/usr/bin/env python
"""
  updater.py

  This file is a part of the AppMetrica.

  Copyright 2017 YANDEX

  You may not use this file except in compliance with the License.
  You may obtain a copy of the License at:
        https://yandex.com/legal/metrica_termsofuse/
"""
import datetime
import logging
from typing import List, Tuple

from pandas import DataFrame

from fields import FieldsCollection, Converter
from logs_api import Loader
from .db_controller import DbController

logger = logging.getLogger(__name__)


class Updater(object):
    def __init__(self, loader: Loader, db_controller: DbController,
                 fields_collection: FieldsCollection):
        self._loader = loader
        self._db_controller = db_controller
        self._fields = fields_collection

    @staticmethod
    def _preprocess(df: DataFrame) -> DataFrame:
        df.drop_duplicates(inplace=True)
        return df

    @staticmethod
    def _append_system_fields(df: DataFrame, app_id: str) -> DataFrame:
        df['app_id'] = app_id
        return df

    @staticmethod
    def _apply_converters(df: DataFrame,
                          converters: List[Tuple[str, Converter]])\
            -> DataFrame:
        for name, converter in converters:
            df[name] = converter(df)
        return df

    def _process_data(self, app_id, df):
        df = df.copy()
        df = self._preprocess(df)
        df = self._append_system_fields(df, app_id)
        df = self._apply_converters(df, self._fields.get_converters())
        return df

    def update(self, app_id: str, date: datetime.date):
        df_it = self._loader.load(app_id, self._fields.source,
                                  self._fields.get_load_fields(), date)
        for df in df_it:
            logger.debug("Start processing data chunk")
            upload_df = self._process_data(app_id, df)
            self._db_controller.insert_data(upload_df, date)
