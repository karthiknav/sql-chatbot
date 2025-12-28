from aws_cdk import (
    Stack,
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnOutput,
    Fn
)
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v34 import KubectlV34Layer


class EksStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Use the passed VPC object directly
        self.vpc = vpc
        
        # Import EKS Kubectl Role from IAM stack
        eks_kubectl_role_arn = Fn.import_value("SqlChatbot-EKSKubectlRoleArn")
        eks_kubectl_role = iam.Role.from_role_arn(self, "EksKubeCtlRole", eks_kubectl_role_arn)
        
        # Import Bedrock Policy from IAM stack
        pod_policy_arn = Fn.import_value("SqlChatbot-PodPolicyArn")
        pod_policy = iam.ManagedPolicy.from_managed_policy_arn(self, "BedrockPolicy", pod_policy_arn)
        
        # Create EKS cluster in private subnets
        self.cluster = eks.Cluster(
            self, "SqlChatbotCluster",
            version=eks.KubernetesVersion.V1_34,
            alb_controller=eks.AlbControllerOptions(
                version=eks.AlbControllerVersion.V2_8_2
            ),
            cluster_name="eks-cdk-sqlchatbot",
            vpc=self.vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)],
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            kubectl_layer=KubectlV34Layer(self, "kubectl-v34-layer"),
            default_capacity=0,  # We'll add managed node group separately
            masters_role=eks_kubectl_role  # Allow cluster role to manage cluster
        )
        
        # Add managed node group
        self.cluster.add_nodegroup_capacity(
            "SqlChatbotNodeGroup",
            instance_types=[ec2.InstanceType("t3.medium")],
            ami_type=eks.NodegroupAmiType.AL2023_X86_64_STANDARD,
            min_size=1,
            max_size=3,
            desired_size=2,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            nodegroup_name="sqlchatbot-nodes"
        )
        
        # Create service account role for Bedrock access
        pod_service_account = self.cluster.add_service_account(
            "sql-chatbot-sa",
            name="sql-chatbot-sa",
            namespace="default"
        )
        
        # Attach the imported Bedrock policy to service account
        pod_service_account.role.add_managed_policy(pod_policy)
        
        # Export service account role ARN
        CfnOutput(
            self, "PodServiceAccountRoleArn",
            value=pod_service_account.role.role_arn,
            export_name="SqlChatbot-PodServiceAccountRoleArn"
        )
    
        
        # Output cluster details
        CfnOutput(
            self, "ClusterName",
            value=self.cluster.cluster_name,
            export_name="SqlChatbot-ClusterName"
        )
        
        CfnOutput(
            self, "ClusterEndpoint",
            value=self.cluster.cluster_endpoint,
            export_name="SqlChatbot-ClusterEndpoint"
        )
        
        CfnOutput(
            self, "ClusterArn",
            value=self.cluster.cluster_arn,
            export_name="SqlChatbot-ClusterArn"
        )