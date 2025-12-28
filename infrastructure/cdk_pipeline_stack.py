from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_ecr as ecr,
    aws_iam as iam,
    Fn
)
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep
from constructs import Construct


class SqlChatbotPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Import EKS Kubectl Role from IAM stack
        eks_kubectl_role_arn = Fn.import_value("SqlChatbot-EKSKubectlRoleArn")
        eks_kubectl_role = iam.Role.from_role_arn(self, "EksKubeCtlRoleCiCd", eks_kubectl_role_arn)
        
        # Import cluster name and service account role from EKS stack
        cluster_name = Fn.import_value("SqlChatbot-ClusterName")
        pod_role_arn = Fn.import_value("SqlChatbot-PodServiceAccountRoleArn")
        
        # Import DB secret ARN from RDS stack
        db_secret_arn = Fn.import_value("SqlChatbot-DbSecretArn")
        
        codebuild_role = iam.Role(
            self, "CodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonElasticContainerRegistryPublicPowerUser")
            ],
            inline_policies={
                "AssumeEksKubeCtlRolePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["sts:AssumeRole"],
                            resources=[f"arn:aws:iam::{self.account}:role/{eks_kubectl_role.role_name}"],
                            effect=iam.Effect.ALLOW
                        )
                    ]
                )
            }
        )
        
        source = CodePipelineSource.connection(
            "karthiknav/sql-chatbot",
            "master",
            connection_arn="arn:aws:codeconnections:us-east-1:206409480438:connection/c12ba6ca-3d36-4ae9-8a2e-51fa31e27866"
        )
        
        pipeline = CodePipeline(
            self, "synth-pipeline-id",
            pipeline_name="sqlChatbotPipeline",
            synth=ShellStep(
                "Synth",
                input=source,
                commands=["pip install aws-cdk-lib", "pip install aws-cdk.lambda-layer-kubectl-v34",
                          "npm install -g aws-cdk", "cdk synth"]
            )
        )
        
        pipeline.build_pipeline()
        underlying_pipeline = pipeline.pipeline
        
        source_artifact = underlying_pipeline.stages[0].actions[0].action_properties.outputs[0]
        
        # Try to use existing ECR repository or create new one
        try:
            ecr_repo = ecr.Repository.from_repository_name(
                self, "SqlChatbotRepository",
                repository_name="sqlchatbot"
            )
        except:
            ecr_repo = ecr.Repository(
                self, "SqlChatbotRepository",
                repository_name="sqlchatbot"
            )
        
        build_project = codebuild.PipelineProject(
            self, "Project",
            role=codebuild_role,
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_4,
                privileged=True,
                environment_variables={
                    "ECR_REGISTRY": codebuild.BuildEnvironmentVariable(value="206409480438.dkr.ecr.us-east-1.amazonaws.com"),
                    "ECR_REPOSITORY": codebuild.BuildEnvironmentVariable(value=ecr_repo.repository_name),
                    "AWS_REGION": codebuild.BuildEnvironmentVariable(value=self.region),
                    "EKS_CLUSTER_NAME": codebuild.BuildEnvironmentVariable(value=cluster_name),
                    "EKS_KUBECTL_ROLE_ARN": codebuild.BuildEnvironmentVariable(value=eks_kubectl_role.role_arn),
                    "BEDROCK_ROLE_ARN": codebuild.BuildEnvironmentVariable(value=pod_role_arn),
                    "DB_SECRET_MANAGER_ARN": codebuild.BuildEnvironmentVariable(value=db_secret_arn)
                }
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            project_name="sqlChatbotBuildProject"
        )
        
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build-Action",
            project=build_project,
            input=source_artifact,
            outputs=[codepipeline.Artifact()]
        )
        
        underlying_pipeline.add_stage(
            stage_name="BuildApp",
            actions=[build_action]
        )