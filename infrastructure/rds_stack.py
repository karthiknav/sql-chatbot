from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2,
    Duration,
    CfnOutput
)
from constructs import Construct


class RdsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Use the passed VPC object directly
        self.vpc = vpc
        
        # Create DB subnet group in private subnets
        db_subnet_group = rds.SubnetGroup(
            self, "DbSubnetGroup",
            description="Subnet group for RDS database",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        )
        
        # Create security group for RDS
        db_security_group = ec2.SecurityGroup(
            self, "DbSecurityGroup",
            vpc=self.vpc,
            description="Security group for RDS PostgreSQL",
            allow_all_outbound=False
        )
        
        # Allow inbound PostgreSQL connections from VPC
        db_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL access from VPC"
        )
        
        # Store security group for bastion access
        self.db_security_group = db_security_group
        
        # Create RDS PostgreSQL instance
        self.database = rds.DatabaseInstance(
            self, "PostgresDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            vpc=self.vpc,
            subnet_group=db_subnet_group,
            security_groups=[db_security_group],
            database_name="dvdrental",
            credentials=rds.Credentials.from_generated_secret("postgres"),
            allocated_storage=20,
            storage_encrypted=True,
            deletion_protection=False,
            backup_retention=Duration.days(7)
        )
        
        # Output database connection details
        CfnOutput(
            self, "DbEndpoint",
            value=self.database.instance_endpoint.hostname,
            export_name="SqlChatbot-DbEndpoint"
        )
        
        CfnOutput(
            self, "DbPort",
            value=str(self.database.instance_endpoint.port),
            export_name="SqlChatbot-DbPort"
        )
        
        CfnOutput(
            self, "DbSecretArn",
            value=self.database.secret.secret_arn,
            export_name="SqlChatbot-DbSecretArn"
        )