import sys

def get_cloud_provider():
    print("Select your cloud provider:")
    print("1. AWS")
    print("2. Azure")
    print("3. GCP")
    choice = input("Enter your choice (1/2/3): ").strip()

    if choice == "1":
        return "AWS"
    elif choice == "2":
        return "Azure"
    elif choice == "3":
        return "GCP"
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)


def aws_cost_optimization():
    services = {
        "EC2": [
            "Use AWS Cost Explorer to identify underutilized instances.",
            "Switch to Reserved Instances or Savings Plans for steady workloads.",
            "Use Spot Instances for non-critical workloads.",
            "Enable auto-scaling to match demand."
        ],
        "S3": [
            "Move infrequently accessed data to S3 Glacier or IA tiers.",
            "Enable S3 lifecycle policies.",
            "Use S3 Intelligent-Tiering for automatic cost optimization."
        ],
        "RDS": [
            "Stop RDS instances during non-business hours.",
            "Use RDS Reserved Instances for predictable workloads.",
            "Enable storage auto-scaling and monitor idle connections."
        ],
        "EKS / ECS": [
            "Use Fargate Spot or EC2 Spot nodes.",
            "Right-size container resources.",
            "Consolidate workloads using cluster autoscaler."
        ]
    }
    return services


def azure_cost_optimization():
    services = {
        "Virtual Machines": [
            "Resize or shut down VMs during off hours using Azure Automation.",
            "Use Azure Reserved VM Instances for long-term savings.",
            "Leverage Azure Spot VMs for non-critical workloads."
        ],
        "Storage Accounts": [
            "Move cool or archive data to cheaper tiers.",
            "Enable Azure Blob lifecycle management policies.",
            "Delete unattached disks."
        ],
        "SQL Database": [
            "Use serverless or elastic pools for variable workloads.",
            "Scale down idle databases.",
            "Set auto-pause for infrequently used databases."
        ],
        "AKS": [
            "Use cluster autoscaler to adjust node count.",
            "Right-size node pools.",
            "Use Spot nodes for non-production workloads."
        ]
    }
    return services


def gcp_cost_optimization():
    services = {
        "Compute Engine": [
            "Use sustained-use and committed-use discounts.",
            "Right-size VMs using Recommender API.",
            "Use preemptible VMs for batch jobs."
        ],
        "Cloud Storage": [
            "Use object lifecycle management for automatic tiering.",
            "Move rarely used data to Nearline or Coldline.",
            "Delete old object versions."
        ],
        "BigQuery": [
            "Use partitioned tables and limit scanned data.",
            "Use flat-rate pricing for predictable workloads.",
            "Monitor queries for inefficiencies."
        ],
        "GKE": [
            "Use cluster autoscaler and node auto-provisioning.",
            "Leverage Spot (preemptible) nodes.",
            "Consolidate workloads on fewer nodes."
        ]
    }
    return services


def display_suggestions(provider, services):
    print(f"\n--- Cost Optimization Suggestions for {provider} ---\n")
    for service, suggestions in services.items():
        print(f"🔹 {service}")
        for tip in suggestions:
            print(f"   - {tip}")
        print()


if __name__ == "__main__":
    provider = get_cloud_provider()
    if provider == "AWS":
        services = aws_cost_optimization()
    elif provider == "Azure":
        services = azure_cost_optimization()
    else:
        services = gcp_cost_optimization()

    display_suggestions(provider, services)
