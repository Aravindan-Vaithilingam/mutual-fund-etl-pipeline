import logging
import time
from pprint import pprint


def execute_query(athena_client, query, output_location):
    try:
        # Define the output location for query results
        output_location = output_location
        # print(QUERY.format( scheme_code, True))
        # Start the query execution
        response = athena_client.start_query_execution(
            QueryString=query,
            ResultConfiguration={
                'OutputLocation': output_location
            }
        )

        # Get the query execution ID
        query_execution_id = response['QueryExecutionId']

        # Wait for the query to complete
        while True:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = response['QueryExecution']['Status']['State']
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(5)
        result_set = []
        # Check the status of the query
        if status == 'SUCCEEDED':
            result_response = athena_client.get_query_results(QueryExecutionId=query_execution_id,
                                                       MaxResults=10)
            pprint(result_response)
            next_token = result_response.get('NextToken')
            result_set.extend(result_response['ResultSet']['Rows'])
            while next_token:
                # for row in response['ResultSet']['Rows']:
                result_response = athena_client.get_query_results(QueryExecutionId=query_execution_id,
                                                             NextToken = next_token, MaxResults=10)
                result_set.extend(result_response['ResultSet']['Rows'])
                next_token = result_response.get('NextToken')
            return result_set
        else:
            print(f'Query failed with status: {status}')
            return False
    except Exception as exc:
        logging.error(exc, exc_info=True)