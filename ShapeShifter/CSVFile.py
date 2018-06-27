import pandas as pd

from SSFile import SSFile


class CSVFile(SSFile):

    def read_input_to_pandas(self, columnList, indexCol):
        if len(columnList) == 0:
            return pd.read_csv(self.filePath, sep="\t")
        return pd.read_csv(self.filePath, usecols=columnList)

    def export_filter_results(self, inputSSFile, gzippedInput=False, columnList=[], query=None, transpose=False, includeAllColumns=False, gzipResults=False, indexCol="Sample"):
        df = None
        includeIndex = False
        null = 'NA'
        query, inputSSFile, df, includeIndex = super().prep_for_export(inputSSFile, gzippedInput, columnList, query,
                                                                       transpose, includeAllColumns, df, includeIndex,
                                                                       indexCol)
        if gzipResults:
            self.filePath = super().__append_gz(self.filePath)
            df.to_csv(path_or_buf=self.filePath, na_rep=null, index=includeIndex, compression='gzip')
        else:
            df.to_csv(path_or_buf=self.filePath, na_rep=null, index=includeIndex)