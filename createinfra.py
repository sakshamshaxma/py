"""
aws_architecture_exporter.py

What it does:
- Scans your AWS account (multiple regions) for common resources (EC2, RDS, EKS, ECS, Lambda, S3, ELB, VPCs, IAM)
- Constructs a Graphviz diagram (grouped by Region -> VPC -> Subnet where possible)
- Renders to aws_architecture.pdf and saves resource metadata to aws_resources.json

Run:
    AWS_PROFILE=yourprofile python aws_architecture_exporter.py
or ensure AWS credentials are available in env or IAM role.
"""

import boto3
import json
import os
import sys
import logging
from graphviz import Digraph
from tqdm import tqdm
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Services to scan per region
REGIONAL_SERVICES = ['ec2', 'rds', 'lambda', 'eks', 'ecs', 'elbv2']  # elbv2 covers ALB/NLB
GLOBAL_SERVICES = ['s3', 'iam']

# Output files
OUT_JSON = "aws_resources.json"
OUT_PDF = "aws_architecture.pdf"
DOT_BASENAME = "aws_architecture"

# Utility: get all commercial regions for ec2 (We'll query ec2.describe_regions)
def get_all_regions():
    try:
        ec2 = boto3.client("ec2")
        resp = ec2.describe_regions(AllRegions=False)
        regions = [r['RegionName'] for r in resp['Regions']]
        logging.info(f"Found {len(regions)} regions: {regions}")
        return regions
    except (NoCredentialsError, ClientError) as e:
        logging.error("Unable to list regions. Check AWS credentials and permissions.")
        raise

# Scanners for each service (best-effort; stable APIs)
def scan_ec2(region, results):
    ec2 = boto3.client("ec2", region_name=region)
    try:
        instances = ec2.describe_instances()
    except Exception as e:
        logging.warning(f"EC2 describe_instances failed in {region}: {e}")
        return
    for res in instances.get('Reservations', []):
        for inst in res.get('Instances', []):
            iid = inst.get('InstanceId')
            vpc = inst.get('VpcId')
            subnet = inst.get('SubnetId')
            state = inst.get('State', {}).get('Name')
            instance_type = inst.get('InstanceType')
            name = next((t['Value'] for t in inst.get('Tags', []) if t.get('Key') == 'Name'), '')
            results['regions'][region]['ec2'].append({
                'InstanceId': iid, 'State': state, 'InstanceType': instance_type,
                'VpcId': vpc, 'SubnetId': subnet, 'Name': name
            })

def scan_rds(region, results):
    rds = boto3.client("rds", region_name=region)
    try:
        dbs = rds.describe_db_instances()
    except Exception as e:
        logging.warning(f"RDS describe_db_instances failed in {region}: {e}")
        return
    for db in dbs.get('DBInstances', []):
        results['regions'][region]['rds'].append({
            'DBInstanceIdentifier': db.get('DBInstanceIdentifier'),
            'Engine': db.get('Engine'),
            'DBInstanceClass': db.get('DBInstanceClass'),
            'VpcId': db.get('DBSubnetGroup', {}).get('VpcId'),
            'Status': db.get('DBInstanceStatus'),
            'MultiAZ': db.get('MultiAZ')
        })

def scan_s3(results):
    s3 = boto3.client("s3")
    try:
        buckets = s3.list_buckets()
    except Exception as e:
        logging.warning(f"S3 list_buckets failed: {e}")
        return
    for b in buckets.get('Buckets', []):
        results['global']['s3'].append({'Name': b['Name'], 'CreationDate': str(b['CreationDate'])})

def scan_lambda(region, results):
    client = boto3.client('lambda', region_name=region)
    try:
        paginator = client.get_paginator('list_functions')
        for page in paginator.paginate():
            for f in page.get('Functions', []):
                results['regions'][region]['lambda'].append({
                    'FunctionName': f.get('FunctionName'),
                    'Runtime': f.get('Runtime'),
                    'VpcConfig': f.get('VpcConfig', {}),
                })
    except Exception as e:
        logging.warning(f"Lambda list_functions failed in {region}: {e}")

def scan_eks(region, results):
    client = boto3.client('eks', region_name=region)
    try:
        clusters = client.list_clusters().get('clusters', [])
        for c in clusters:
            info = client.describe_cluster(name=c).get('cluster', {})
            results['regions'][region]['eks'].append({
                'Name': c,
                'Version': info.get('version'),
                'VpcId': info.get('resourcesVpcConfig', {}).get('vpcId'),
                'Subnets': info.get('resourcesVpcConfig', {}).get('subnetIds', []),
            })
    except Exception as e:
        logging.debug(f"EKS list/describe failed in {region}: {e}")

def scan_ecs(region, results):
    client = boto3.client('ecs', region_name=region)
    try:
        clusters = client.list_clusters().get('clusterArns', [])
        for arn in clusters:
            summary = client.describe_clusters(clusters=[arn]).get('clusters', [])[0]
            results['regions'][region]['ecs'].append({
                'ClusterArn': arn,
                'ClusterName': summary.get('clusterName'),
                'Status': summary.get('status'),
                'RegisteredContainerInstancesCount': summary.get('registeredContainerInstancesCount')
            })
    except Exception as e:
        logging.debug(f"ECS list/describe failed in {region}: {e}")

def scan_elbv2(region, results):
    client = boto3.client('elbv2', region_name=region)
    try:
        lbs = client.describe_load_balancers().get('LoadBalancers', [])
        for lb in lbs:
            results['regions'][region]['elbv2'].append({
                'LoadBalancerName': lb.get('LoadBalancerName'),
                'Type': lb.get('Type'),
                'Scheme': lb.get('Scheme'),
                'VpcId': lb.get('VpcId'),
                'DNSName': lb.get('DNSName')
            })
    except Exception as e:
        logging.debug(f"ELBv2 describe failed in {region}: {e}")

def scan_vpcs(region, results):
    client = boto3.client('ec2', region_name=region)
    try:
        vpcs = client.describe_vpcs().get('Vpcs', [])
        subnets = client.describe_subnets().get('Subnets', [])
    except Exception as e:
        logging.debug(f"VPC/Subnet describe failed in {region}: {e}")
        return
    for v in vpcs:
        vid = v.get('VpcId')
        results['regions'][region]['vpcs'][vid] = {
            'CidrBlock': v.get('CidrBlock'),
            'IsDefault': v.get('IsDefault'),
            'Tags': v.get('Tags', []),
            'Subnets': []
        }
    for s in subnets:
        sid = s.get('SubnetId')
        vid = s.get('VpcId')
        if vid in results['regions'][region]['vpcs']:
            results['regions'][region]['vpcs'][vid]['Subnets'].append({
                'SubnetId': sid, 'CidrBlock': s.get('CidrBlock'), 'AvailabilityZone': s.get('AvailabilityZone')
            })

def scan_iam(results):
    client = boto3.client('iam')
    try:
        users = client.list_users().get('Users', [])
        roles = client.list_roles().get('Roles', [])
        policies = client.list_policies(Scope='Local').get('Policies', [])
        results['global']['iam'] = {
            'UsersCount': len(users),
            'RolesCount': len(roles),
            'ManagedPoliciesCount': len(policies)
        }
    except Exception as e:
        logging.debug(f"IAM list failed: {e}")

# Main scanner orchestration
def scan_account(regions=None):
    results = {'regions': {}, 'global': {'s3': [], 'iam': {}}}
    if not regions:
        regions = get_all_regions()
    # Initialize region containers
    for r in regions:
        results['regions'][r] = {
            'ec2': [], 'rds': [], 'lambda': [], 'eks': [], 'ecs': [], 'elbv2': [],
            'vpcs': {}
        }

    for r in tqdm(regions, desc="Scanning regions"):
        try:
            # VPCs first to allow mapping
            scan_vpcs(r, results)
            scan_ec2(r, results)
            scan_rds(r, results)
            scan_lambda(r, results)
            scan_eks(r, results)
            scan_ecs(r, results)
            scan_elbv2(r, results)
        except EndpointConnectionError:
            logging.warning(f"Region {r} not accessible in this account/region.")
        except Exception as exc:
            logging.debug(f"Unhandled scanning error in {r}: {exc}")

    # Global scans
    scan_s3(results)
    scan_iam(results)

    # Save JSON
    with open(OUT_JSON, "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    logging.info(f"Saved resource metadata to {OUT_JSON}")
    return results

# Build Graphviz diagram (best-effort relationships)
def build_graph(results):
    dot = Digraph(name="AWS_Architecture", format="pdf")
    dot.attr(rankdir='LR', splines='ortho')
    dot.attr('node', shape='box')

    # Global cluster for S3 / IAM
    with dot.subgraph(name='cluster_global') as g:
        g.attr(label='Global')
        # S3
        if results['global']['s3']:
            with g.subgraph(name='cluster_s3') as s3c:
                s3c.attr(label='S3 Buckets')
                for b in results['global']['s3']:
                    bnode = f"s3:{b['Name']}"
                    s3c.node(bnode, label=f"S3\n{b['Name']}")
        # IAM summary (single node)
        iam_summary = results['global'].get('iam', {})
        g.node('iam', label=f"IAM\nUsers:{iam_summary.get('UsersCount', '?')} Roles:{iam_summary.get('RolesCount', '?')}")

    # Regions
    for region, data in results['regions'].items():
        with dot.subgraph(name=f'cluster_{region}') as rg:
            rg.attr(label=f"Region: {region}")
            # VPC clusters
            if data['vpcs']:
                for vpc_id, vpc_info in data['vpcs'].items():
                    cname = f"cluster_{region}_{vpc_id.replace('-', '_')}"
                    with rg.subgraph(name=cname) as vcl:
                        vcl.attr(label=f"VPC {vpc_id}\n{vpc_info.get('CidrBlock','')}")
                        # Subnets as nodes (optional)
                        for subnet in vpc_info.get('Subnets', []):
                            sn = f"{region}_{subnet['SubnetId']}"
                            vcl.node(sn, label=f"Subnet\n{subnet['SubnetId']}\n{subnet.get('AvailabilityZone')}")
                        # Attach EC2 instances that belong to this VPC
                        for ec2i in [e for e in data['ec2'] if e.get('VpcId') == vpc_id]:
                            nid = f"{region}_{ec2i['InstanceId']}"
                            label = f"EC2\n{ec2i['InstanceId']}\n{ec2i.get('InstanceType')}\n{ec2i.get('State')}"
                            vcl.node(nid, label=label)
                            # edge to subnet
                            if ec2i.get('SubnetId'):
                                sn = f"{region}_{ec2i['SubnetId']}"
                                vcl.edge(sn, nid)
                        # Attach RDS in same VPC
                        for rdsinst in [r for r in data['rds'] if r.get('VpcId') == vpc_id]:
                            rid = f"{region}_rds_{rdsinst['DBInstanceIdentifier']}"
                            vcl.node(rid, label=f"RDS\n{rdsinst['DBInstanceIdentifier']}\n{rdsinst.get('Engine')}")
                # EC2 not in any VPC (rare)
            else:
                # If no VPC data, just list EC2 etc at region level
                for ec2i in data['ec2']:
                    nid = f"{region}_{ec2i['InstanceId']}"
                    rg.node(nid, label=f"EC2\n{ec2i['InstanceId']}\n{ec2i.get('InstanceType')}\n{ec2i.get('State')}")

            # Load balancers
            for lb in data['elbv2']:
                lid = f"{region}_lb_{lb['LoadBalancerName']}"
                rg.node(lid, label=f"LB\n{lb['LoadBalancerName']}\n{lb['Type']}\n{lb.get('DNSName')}")
                # connect LB to VPC node (if known)
                if lb.get('VpcId') and lb.get('VpcId') in data['vpcs']:
                    # make a small edge to the VPC cluster label node
                    rg.edge(lid, f"cluster_{region}_{lb['VpcId'].replace('-', '_')}")
            # EKS clusters
            for eks in data['eks']:
                eid = f"{region}_eks_{eks['Name']}"
                rg.node(eid, label=f"EKS\n{eks['Name']}\nver:{eks.get('Version')}")
                if eks.get('VpcId'):
                    rg.edge(eid, f"cluster_{region}_{eks['VpcId'].replace('-', '_')}")
            # ECS clusters
            for ecs in data['ecs']:
                cid = f"{region}_ecs_{ecs['ClusterName']}"
                rg.node(cid, label=f"ECS\n{ecs['ClusterName']}\n{ecs.get('Status')}")
            # Lambdas (map VPC if present)
            for lam in data['lambda']:
                lid = f"{region}_lambda_{lam['FunctionName']}"
                rg.node(lid, label=f"Lambda\n{lam['FunctionName']}\n{lam.get('Runtime')}")
                vpccfg = lam.get('VpcConfig') or {}
                if vpccfg.get('VpcId'):
                    rg.edge(lid, f"cluster_{region}_{vpccfg['VpcId'].replace('-', '_')}")
            # RDS already attached inside vpc clusters earlier if vpc info existed

    # Optional edges: connect IAM to resources (indicates auth)
    dot.edge('iam', 's3:' + results['global']['s3'][0]['Name'] if results['global']['s3'] else 'iam', label='auth (example)')

    return dot

# Entrypoint
def main():
    try:
        regions = None
        print("This script will scan all regions returned by EC2.describe_regions() in your AWS account.")
        print("Make sure AWS credentials are configured (env, ~/.aws/credentials or role).")
        proceed = input("Proceed? (y/N): ").strip().lower()
        if proceed != 'y':
            print("Aborted by user.")
            sys.exit(0)

        results = scan_account(regions)
        dot = build_graph(results)
        # Render PDF
        outpath = dot.render(filename=DOT_BASENAME, cleanup=True)
        # dot.render writes DOT and PDF, cleanup removes DOT, returns filename with .pdf extension
        pdf_file = outpath if outpath.endswith('.pdf') else DOT_BASENAME + '.pdf'
        if os.path.exists(pdf_file):
            print(f"Architecture PDF generated: {pdf_file}")
        else:
            print("PDF render may have failed. Check Graphviz installation and permissions.")
    except NoCredentialsError:
        logging.error("AWS credentials not found. Configure credentials before running.")
    except Exception as ex:
        logging.exception(f"Unhandled error: {ex}")

if __name__ == "__main__":
    main()
