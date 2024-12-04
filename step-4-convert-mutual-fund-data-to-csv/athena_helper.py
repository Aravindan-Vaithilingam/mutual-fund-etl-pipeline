import logging
import time


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

        # Check the status of the query
        if status == 'SUCCEEDED':
            print('Query succeeded')
            return True
        else:
            print(f'Query failed with status: {status}')
            return False
    except Exception as exc:
        logging.error(exc, exc_info=True)