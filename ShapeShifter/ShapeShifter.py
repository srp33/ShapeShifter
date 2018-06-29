

import SSFile


class ShapeShifter:

    def __init__(self, filePath, fileType):
        """
        Creates a ShapeShifter object
        :param filePath: string name of a file path to read and perform operations on
        :param fileType: FileTypeEnum indicating the type of file that is being read
        :param index:
        """
        self.inputFile = SSFile.SSFile.factory(filePath, fileType)
        self.gzippedInput= self.__is_gzipped()
        self.outputFile= None

    def export_filter_results(self, outFilePath, outFileType, filters=None, columns=[],
                              transpose=False, includeAllColumns=False, gzipResults=False, index='Sample'):
        """
        Filters and then exports data to a file
        :param outFilePath: Name of the file that results will be saved to
        :param outFileType: FileTypeEnum indicating what file format results will be saved to
        :param filters: string representing the query or filter to apply to the data set
        :param columns: list of columns to include in the output. If blank, all columns will be included.
        :param transpose: boolean when, if True, index and columns will be transposed in the output file
        :param includeAllColumns: boolean indicating whether to include all columns in the output. If True, overrides columnList
        :param gzipResults: boolean indicating whether the resulting file will be gzipped
        :return:
        """
        #todo: perhaps not require the outFileType to be specified; infer it from outFilePath?
        self.outputFile = SSFile.SSFile.factory(outFilePath,outFileType)
        self.outputFile.export_filter_results(self.inputFile, gzippedInput=self.gzippedInput, columnList=columns, query=filters, transpose=transpose, includeAllColumns=includeAllColumns, gzipResults=gzipResults, indexCol=index)

    def export_query_results(self, outFilePath, outFileType, columns: list = [],
                             continuousQueries: list = [], discreteQueries: list = [], transpose=False,
                             includeAllColumns=False, gzipResults = False):
        """
        Filters and exports data to a file. Similar to export_filter_results, but takes filters in the form of ContinuousQuery and DiscreteQuery objects,
        and has slightly less flexible functionality
        :param outFilePath: Name of the file that results will be saved to
        :param outFileType: FileTypeEnum indicating what file format results will be saved to
        :param columns: list of columns to include in the output. If blank, all columns will be included.
        :param continuousQueries: list of ContinuousQuery objects representing queries on a column of continuous data
        :param discreteQueries: list of DiscreteQuery objects representing queries on a column of discrete data
        :param transpose: boolean when, if True, index and columns will be transposed in the output file
        :param includeAllColumns: boolean indicating whether to include all columns in the output. If True, overrides columnList
        :param gzipResults: boolean indicating whether the resulting file will be gzipped
        :return:
        """

        self.outputFile = SSFile.SSFile.factory(outFilePath, outFileType)
        query = self.__convert_queries_to_string(continuousQueries, discreteQueries)
        self.export_filter_results( columns=columns, filters=query,
                              transpose=transpose, includeAllColumns=includeAllColumns, gzipResults=gzipResults)

    def __is_gzipped(self):
        """
        Function for internal use. Checks if a file is gzipped based on its extension
        """
        extensions = self.inputFile.filePath.rstrip("\n").split(".")
        if extensions[len(extensions) - 1] == 'gz':
            return True
        return False

    def __convert_queries_to_string(self, continuousQueries: list = [], discreteQueries: list = []):
        """
        Function for internal use. Given a list of ContinuousQuery objects and DiscreteQuery objects, returns a single string representing all given queries
        """

        if len(continuousQueries) == 0 and len(discreteQueries) == 0:
            return None

        completeQuery = ""
        for i in range(0, len(continuousQueries)):
            completeQuery += continuousQueries[i].columnName + self.__operator_enum_converter(
                continuousQueries[i].operator) + str(continuousQueries[i].value)
            if i < len(continuousQueries) - 1 or len(discreteQueries) > 0:
                completeQuery += " and "

        for i in range(0, len(discreteQueries)):
            completeQuery += "("
            for j in range(0, len(discreteQueries[i].values)):
                completeQuery += discreteQueries[i].columnName + "==" + "'" + discreteQueries[i].values[j] + "'"
                if j < len(discreteQueries[i].values) - 1:
                    completeQuery += " or "
            completeQuery += ")"
            if i < len(discreteQueries) - 1:
                completeQuery += " and "
        # print(completeQuery)
        return completeQuery

    def __operator_enum_converter(self, operator):
        """
        Function for internal use. Used to translate an OperatorEnum into a string representation of that operator
        """
        import OperatorEnum
        if operator == OperatorEnum.OperatorEnum.Equals:
            return "=="
        elif operator == OperatorEnum.OperatorEnum.GreaterThan:
            return ">"
        elif operator == OperatorEnum.OperatorEnum.GreaterThanOrEqualTo:
            return ">="
        elif operator == OperatorEnum.OperatorEnum.LessThan:
            return "<"
        elif operator == OperatorEnum.OperatorEnum.LessThanOrEqualTo:
            return "<="
        elif operator == OperatorEnum.OperatorEnum.NotEquals:
            return "!="


########################################################################################################################

    ####### All of the following functions are designed for parquet only right now
    #todo: clean up all the documentation here

    def get_column_names(self) -> list:
        """
        Retrieves all column names from a dataset stored in a parquet file
        :type parquetFilePath: string
        :param parquetFilePath: filepath to a parquet file to be examined

        :return: All column names
        :rtype: list

        """
        import pyarrow.parquet as pq
        p = pq.ParquetFile(self.inputFile.filePath)
        columnNames = p.schema.names
        # delete 'Sample' from schema
        del columnNames[0]

        # delete extraneous other schema that the parquet file tacks on at the end
        if '__index_level_' in columnNames[len(columnNames) - 1]:
            del columnNames[len(columnNames) - 1]
        if 'Unnamed:' in columnNames[len(columnNames) - 1]:
            del columnNames[len(columnNames) - 1]
        return columnNames


    def peek(self, numRows=10, numCols=10):
        """
        Takes a look at the first few rows and columns of a parquet file and returns a pandas dataframe corresponding to the number of requested rows and columns

        :type parquetFilePath: string
        :param parquetFilePath: filepath to a parquet file to be examined

        :type numRows: int
        :param numRows: the number of rows the returned Pandas dataframe will contain

        :type numCols: int
        :param numCols: the number of columns the returned Pandas dataframe will contain

        :return: The first numRows and numCols in the given parquet file
        :rtype: Pandas dataframe
        """
        allCols = self.get_column_names()
        if (numCols > len(allCols)):
            numCols = len(allCols)
        selectedCols = []
        selectedCols.append(self.index)
        for i in range(0, numCols):
            selectedCols.append(allCols[i])
        df = pd.read_parquet(self.inputFile.filePath, columns=selectedCols)
        df.set_index(self.index, drop=True, inplace=True)
        df = df.iloc[0:numRows, 0:numCols]
        return df

    def peek_by_column_names(self, listOfColumnNames, numRows=10):
        """
        Peeks into a parquet file by looking at a specific set of columns

        :type parquetFilePath: string
        :param parquetFilePath: filepath to a parquet file to be examined

        :type numRows: int
        :param numRows: the number of rows the returned Pandas dataframe will contain

        :return: The first numRows of all the listed columns in the given parquet file
        :rtype: Pandas dataframe

        """
        listOfColumnNames.insert(0, self.index)
        df = pd.read_parquet(self.inputFile.filePath, columns=listOfColumnNames)
        df.set_index(self.index, drop=True, inplace=True)
        df = df[0:numRows]
        return df

    def get_column_info(self, columnName: str, sizeLimit: int = None):
        """
        Retrieves a specified column's name, data type, and all its unique values from a parquet file

        :type parquetFilePath: string
        :param parquetFilePath: filepath to a parquet file to be examined

        :type columnName: string
        :param columnName: the name of the column about which information is being obtained

        :type sizeLimit: int
        :param sizeLimit: limits the number of unique values returned to be no more than this number

        :return: Name, data type (continuous/discrete), and unique values from specified column
        :rtype: ColumnInfo object
        """
        import ColumnInfo
        columnList = [columnName]
        df = pd.read_parquet(self.inputFile.filePath, columns=columnList)

        # uniqueValues = set()
        # for index, row in df.iterrows():
        # 	try:
        # 		uniqueValues.add(row[columnName])
        # 	except (TypeError, KeyError) as e:
        # 		return None
        # 	if sizeLimit != None:
        # 		if len(uniqueValues)>=sizeLimit:
        # 			break
        # uniqueValues = list(uniqueValues)

        uniqueValues = df[columnName].unique().tolist()
        # uniqueValues.remove(None)
        # Todo: There is probably a better way to do this...
        i = 0
        while uniqueValues[i] == None:
            i += 1
        if isinstance(uniqueValues[i], str) or isinstance(uniqueValues[i], bool):
            return ColumnInfo.ColumnInfo(columnName, "discrete", uniqueValues)
        else:
            return ColumnInfo.ColumnInfo(columnName, "continuous", uniqueValues)

    def get_all_columns_info(self):
        """
        Retrieves the column name, data type, and all unique values from every column in a file

        :type parquetFilePath: string
        :param parquetFilePath: filepath to a parquet file to be examined

        :return: Name, data type (continuous/discrete), and unique values from every column
        :rtype: dictionary where key: column name and value:ColumnInfo object containing the column name, data type (continuous/discrete), and unique values from all columns
        """
        # columnNames = getColumnNames(parquetFilePath)
        import ColumnInfo
        df = pd.read_parquet(self.inputFile.filePath)
        columnDict = {}
        for col in df:
            uniqueValues = df[col].unique().tolist()
            i = 0
            while uniqueValues[i] == None:
                i += 1
            if isinstance(uniqueValues[i], str) or isinstance(uniqueValues[i], bool):
                columnDict[col] = ColumnInfo.ColumnInfo(col, "discrete", uniqueValues)
            else:
                columnDict[col] = ColumnInfo.ColumnInfo(col, "continuous", uniqueValues)
        return columnDict

import pandas as pd