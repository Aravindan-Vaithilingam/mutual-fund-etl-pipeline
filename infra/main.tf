terraform {
  backend "s3" {
    bucket = "xxxxxxxx-dev-space"
    key    = "mtf-data-pipeline/terraform/state/terraform.tfstate"
    region = "ap-south-1"
  }
}


provider "aws" {
  region = "ap-south-1"
}






resource "aws_sqs_queue" "mutual_fund_scheme_code" {
  name                       = "mutual-fund-scheme-code"
  delay_seconds              = 0
  max_message_size           = 262144 # Maximum message size (262144 bytes)
  message_retention_seconds  = 86400  # Retain messages for 1 day
  visibility_timeout_seconds = 600
  receive_wait_time_seconds  = 0
}

resource "aws_lambda_layer_version" "requests_layer" {
  s3_bucket           = "xxxxxxxx-dev-space"
  s3_key              = "mtf-data-pipeline/code/lambda_layers/requests.zip"
  layer_name          = "requests"
  compatible_runtimes = ["python3.12"]
}


# Step 1 resources
resource "aws_lambda_function" "step_1_collect_mutual_fund_list_data" {
  function_name = "step-1-collect-mutual-fund-list-data"
  handler       = "index.lambda_handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn
  s3_bucket     = "xxxxxxxx-dev-space"
  s3_key        = "mtf-data-pipeline/code/step-1-collect-mutual-fund-list-data.zip"
  layers = [aws_lambda_layer_version.requests_layer.arn,
  "arn:aws:lambda:ap-south-1:xxxxxxxxxxxxx5:layer:AWSSDKPandas-Python312:13"]
      environment {
    variables = {
      BUCKET_NAME = "xxxxxxxx-dev-space"
      KEY_PREFIX = "mutual-fund-data-pipeline/scheme_list_data"
    }
  }
}



# Event rule to trigger step 1
resource "aws_cloudwatch_event_rule" "trigger_step_1" {
  name                = "trigger_step_1"
  schedule_expression = "cron(0 12 * * ? *)" # Runs daily at 12:00 PM UTC
}

# Set the event target
resource "aws_cloudwatch_event_target" "trigger_step_1" {
  rule = aws_cloudwatch_event_rule.trigger_step_1.name
  arn  = aws_lambda_function.step_1_collect_mutual_fund_list_data.arn
}

# Set the event handler
resource "aws_lambda_permission" "allow_cloudwatch_step_1" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.step_1_collect_mutual_fund_list_data.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_step_1.arn
}


# Step 2 resources

resource "aws_lambda_function" "step_2_identify_new_schemes" {
  function_name = "step-2-identify-new-schemes"
  handler       = "index.handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn
  s3_bucket     = "xxxxxxxx-dev-space"
  s3_key        = "mtf-data-pipeline/code/step-2-identify-new-schemes.zip"
      environment {
    variables = {
      BUCKET_NAME = "xxxxxxxx-dev-space"
      KEY_PREFIX = "mutual-fund-data-pipeline/scheme_list_data"
      QUEUE_URL = aws_sqs_queue.mutual_fund_scheme_code.url
    }
  }
}


resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = "xxxxxxxx-dev-space"

  lambda_function {
    lambda_function_arn = aws_lambda_function.step_2_identify_new_schemes.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.step_2_identify_new_schemes.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::xxxxxxxx-dev-space"
}



# Step 3

resource "aws_lambda_function" "step_3_crawl_nav_data" {
  function_name = "step-3-crawl-nav-data"
  handler       = "index.handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn
  s3_bucket     = "xxxxxxxx-dev-space"
  s3_key        = "mtf-data-pipeline/code/step-3-crawl-nav-data.zip"
  layers        = [aws_lambda_layer_version.requests_layer.arn, "arn:aws:lambda:ap-south-1:xxxxxxxxxxxxx5:layer:AWSSDKPandas-Python312:13"]
        environment {
    variables = {
      BUCKET_NAME = "xxxxxxxx-dev-space"
      KEY_PREFIX = "mutual-fund-data-pipeline/scheme_list_data"
      QUEUE_URL = aws_sqs_queue.mutual_fund_scheme_code.url
      NAV_HISTORY_API = "https://api.mfapi.in/mf/{}" 
      NAV_LIVE_API = " 'https://api.mfapi.in/mf/{}/latest"
    }
  }
}



# Event rule to trigger step 3
resource "aws_cloudwatch_event_rule" "trigger_step_3" {
  name                = "trigger_step_3"
  schedule_expression = "cron(0 1 * * ? *)" # Runs daily at 12:00 PM UTC
}

# Set the event target
resource "aws_cloudwatch_event_target" "trigger_step_3" {
  rule = aws_cloudwatch_event_rule.trigger_step_3.name
  arn  = aws_lambda_function.step_3_crawl_nav_data.arn
}

# Set the event handler
resource "aws_lambda_permission" "allow_cloudwatch_step_3" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.step_3_crawl_nav_data.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_step_3.arn
}



# Step 4

resource "aws_lambda_function" "step_4_convert_mutual_fund_data_to_csv" {
  function_name = "step-4-convert-mutual-fund-data-to-csv"
  handler       = "index.handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn
  s3_bucket     = "xxxxxxxx-dev-space"
  s3_key        = "mtf-data-pipeline/code/step-4-convert-mutual-fund-data-to-csv.zip"
  layers        = [aws_lambda_layer_version.requests_layer.arn, "arn:aws:lambda:ap-south-1:xxxxxxxxxxxxx5:layer:AWSSDKPandas-Python312:13"]
     environment {
    variables = {
      BUCKET_NAME = "xxxxxxxx-dev-space"
      KEY_PREFIX = "mutual-fund-data-pipeline/scheme_list_data"
      BACKUP_KEY_PREFIX = ""
      METADATA_OUTPUT_KEY_PREFIX = ""
      NAV_OUTPUT_KEY_PREFIX = ""
      QUERY = "INSERT INTO mutual_fund_db.historical_data_status VALUES ({0},{1});"
      OUTPUT_LOCATION = ""
    }
  }
}



# Event rule to trigger step 4
resource "aws_cloudwatch_event_rule" "trigger_step_4" {
  name                = "trigger_step_4"
  schedule_expression = "cron(0 1 * * ? *)" # Runs daily at 12:00 PM UTC
}

# Set the event target
resource "aws_cloudwatch_event_target" "trigger_step_4" {
  rule = aws_cloudwatch_event_rule.trigger_step_4.name
  arn  = aws_lambda_function.step_4_convert_mutual_fund_data_to_csv.arn
}

# Set the event handler
resource "aws_lambda_permission" "allow_cloudwatch_step_4" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.step_4_convert_mutual_fund_data_to_csv.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_step_4.arn
}



resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role_for_mf_pipeline"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_exec_policy" {
  name = "lambda_exec_policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "s3:Put*",
          "s3:Get*",
          "s3:List*",
          "s3:DeleteObject"
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::xxxxxxxx-dev-space/mtf-data-pipeline/*"
        ]
      },
      {
        Action = ["sqs:*"]
        Effect = "Allow"
        Resource = [
          aws_sqs_queue.mutual_fund_scheme_code.arn
        ]

      }
    ]
  })
}
