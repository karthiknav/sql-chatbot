from aws_cdk import (
    Stack,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct


class IamStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create EKS Kubectl Role
        self.eks_kubectl_role = iam.Role(
            self, "EKSKubectlRole",
            role_name="EKSKubectlRoleCiCd",
            assumed_by=iam.CompositePrincipal(
                iam.AccountRootPrincipal(),
                iam.ServicePrincipal("eks.amazonaws.com")
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy")
            ],
            inline_policies={
                "EKSDescribePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["eks:Describe*"],
                            resources=["*"],
                            effect=iam.Effect.ALLOW
                        )
                    ]
                )
            }
        )
        
        # Create Bedrock Service Account Role Policy
        self.pod_policy = iam.ManagedPolicy(
            self, "serviceAccountPolicy",
            managed_policy_name="SqlChatbot-ServiceAccountPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret"
                    ],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                )
            ]
        )
        
        # Export role ARN and policy ARN
        CfnOutput(
            self, "EKSKubectlRoleArn",
            value=self.eks_kubectl_role.role_arn,
            export_name="SqlChatbot-EKSKubectlRoleArn"
        )
        
        CfnOutput(
            self, "PodPolicyArn",
            value=self.pod_policy.managed_policy_arn,
            export_name="SqlChatbot-PodPolicyArn"
        )