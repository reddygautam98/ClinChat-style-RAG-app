"""
CloudFormation template for HIPAA-compliant infrastructure
"""
hipaa_infrastructure_template = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "HIPAA-compliant infrastructure for HealthAI application",
    "Parameters": {
        "Environment": {
            "Type": "String",
            "Default": "production",
            "AllowedValues": ["development", "staging", "production"]
        }
    },
    "Resources": {
        # KMS Key for PHI Encryption
        "PHIEncryptionKey": {
            "Type": "AWS::KMS::Key",
            "Properties": {
                "Description": "KMS Key for HIPAA PHI data encryption",
                "KeyPolicy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "Enable IAM User Permissions",
                            "Effect": "Allow",
                            "Principal": {"AWS": {"Fn::Sub": "arn:aws:iam::${AWS::AccountId}:root"}},
                            "Action": "kms:*",
                            "Resource": "*"
                        },
                        {
                            "Sid": "Allow HealthAI Application",
                            "Effect": "Allow",
                            "Principal": {"AWS": {"Ref": "HealthAIApplicationRole"}},
                            "Action": [
                                "kms:Encrypt",
                                "kms:Decrypt",
                                "kms:ReEncrypt*",
                                "kms:GenerateDataKey*",
                                "kms:DescribeKey"
                            ],
                            "Resource": "*"
                        }
                    ]
                },
                "KeyRotationStatus": True,
                "Tags": [
                    {"Key": "Purpose", "Value": "HIPAA-PHI-Encryption"},
                    {"Key": "Compliance", "Value": "HIPAA"},
                    {"Key": "Environment", "Value": {"Ref": "Environment"}}
                ]
            }
        },
        
        # S3 Bucket for HIPAA Audit Logs
        "HIPAAAuditLogsBucket": {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": {"Fn::Sub": "healthai-hipaa-audit-logs-${Environment}"},
                "BucketEncryption": {
                    "ServerSideEncryptionConfiguration": [{
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "aws:kms",
                            "KMSMasterKeyID": {"Ref": "PHIEncryptionKey"}
                        },
                        "BucketKeyEnabled": True
                    }]
                },
                "VersioningConfiguration": {
                    "Status": "Enabled"
                },
                "LifecycleConfiguration": {
                    "Rules": [{
                        "Id": "HIPAA-Retention-Policy",
                        "Status": "Enabled",
                        "ExpirationInDays": 2190,  # 6 years retention
                        "NoncurrentVersionExpirationInDays": 30,
                        "Transitions": [
                            {
                                "TransitionInDays": 30,
                                "StorageClass": "STANDARD_IA"
                            },
                            {
                                "TransitionInDays": 90,
                                "StorageClass": "GLACIER"
                            },
                            {
                                "TransitionInDays": 365,
                                "StorageClass": "DEEP_ARCHIVE"
                            }
                        ]
                    }]
                },
                "NotificationConfiguration": {
                    "CloudWatchConfigurations": [{
                        "Event": "s3:ObjectCreated:*",
                        "CloudWatchConfiguration": {
                            "LogGroupName": {"Ref": "HIPAAAuditLogGroup"}
                        }
                    }]
                },
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True
                },
                "Tags": [
                    {"Key": "Purpose", "Value": "HIPAA-Audit-Logs"},
                    {"Key": "Compliance", "Value": "HIPAA"},
                    {"Key": "DataClassification", "Value": "Confidential"}
                ]
            }
        },
        
        # CloudWatch Log Group for HIPAA Events
        "HIPAAAuditLogGroup": {
            "Type": "AWS::Logs::LogGroup",
            "Properties": {
                "LogGroupName": "/aws/healthai/hipaa-audit",
                "RetentionInDays": 2190,  # 6 years
                "KmsKeyId": {"Fn::GetAtt": ["PHIEncryptionKey", "Arn"]}
            }
        },
        
        # IAM Role for HealthAI Application
        "HealthAIApplicationRole": {
            "Type": "AWS::IAM::Role",
            "Properties": {
                "RoleName": {"Fn::Sub": "HealthAI-Application-Role-${Environment}"},
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }]
                },
                "ManagedPolicyArns": [
                    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
                ],
                "Policies": [{
                    "PolicyName": "HIPAA-Compliance-Policy",
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "HIPAAAuditLogging",
                                "Effect": "Allow",
                                "Action": [
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents",
                                    "s3:PutObject",
                                    "s3:PutObjectAcl"
                                ],
                                "Resource": [
                                    {"Fn::GetAtt": ["HIPAAAuditLogGroup", "Arn"]},
                                    {"Fn::Sub": "${HIPAAAuditLogsBucket}/*"}
                                ]
                            },
                            {
                                "Sid": "KMSEncryption",
                                "Effect": "Allow",
                                "Action": [
                                    "kms:Encrypt",
                                    "kms:Decrypt",
                                    "kms:ReEncrypt*",
                                    "kms:GenerateDataKey*",
                                    "kms:DescribeKey"
                                ],
                                "Resource": {"Ref": "PHIEncryptionKey"}
                            }
                        ]
                    }
                }],
                "Tags": [
                    {"Key": "Purpose", "Value": "HIPAA-Application-Access"},
                    {"Key": "Compliance", "Value": "HIPAA"}
                ]
            }
        },
        
        # CloudTrail for Additional Audit Logging
        "HIPAACloudTrail": {
            "Type": "AWS::CloudTrail::Trail",
            "Properties": {
                "TrailName": {"Fn::Sub": "HealthAI-HIPAA-CloudTrail-${Environment}"},
                "S3BucketName": {"Ref": "HIPAAAuditLogsBucket"},
                "S3KeyPrefix": "cloudtrail-logs/",
                "IncludeGlobalServiceEvents": True,
                "IsLogging": True,
                "IsMultiRegionTrail": True,
                "EnableLogFileValidation": True,
                "KMSKeyId": {"Ref": "PHIEncryptionKey"},
                "EventSelectors": [{
                    "ReadWriteType": "All",
                    "IncludeManagementEvents": True,
                    "DataResources": [
                        {
                            "Type": "AWS::S3::Object",
                            "Values": [{"Fn::Sub": "${HIPAAAuditLogsBucket}/*"}]
                        }
                    ]
                }]
            }
        }
    },
    
    "Outputs": {
        "PHIEncryptionKeyId": {
            "Description": "KMS Key ID for PHI encryption",
            "Value": {"Ref": "PHIEncryptionKey"},
            "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-PHI-Key"}}
        },
        "AuditLogsBucket": {
            "Description": "S3 bucket for HIPAA audit logs",
            "Value": {"Ref": "HIPAAAuditLogsBucket"},
            "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-Audit-Bucket"}}
        },
        "ApplicationRoleArn": {
            "Description": "IAM role for HealthAI application",
            "Value": {"Fn::GetAtt": ["HealthAIApplicationRole", "Arn"]},
            "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-App-Role"}}
        }
    }
}