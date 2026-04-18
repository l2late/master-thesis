import wandb

api = wandb.Api()
entity = "your_entity_name"
project = "your_project_name"

# 1. Iterate over all artifact types (e.g., "model", "dataset")
for artifact_type in api.artifact_types(f"{entity}/{project}"):
    print(f"Scanning artifact type: {artifact_type.name}")

    # 2. Iterate over all collections within the type
    for collection in artifact_type.collections():
        # 3. Iterate over all versions in the collection
        for version in collection.versions():
            # Condition A: Artifact has no aliases (e.g., 'latest' or 'best' was moved)
            if len(version.aliases) == 0:
                print(f"Deleting unaliased artifact: {version.name}")
                version.delete()
                continue

            # Condition B: Artifact is orphaned (the run that created it was deleted)
            # logged_by() returns None if the run no longer exists
            creator_run = version.logged_by()
            consumers = version.used_by()

            if creator_run is None and len(consumers) == 0:
                print(f"Deleting orphaned artifact: {version.name}")
                # delete_aliases=True forces deletion even if the 'latest' tag is still attached
                version.delete(delete_aliases=True)

        # Optional: Delete the collection itself if it is now empty
        # if len(list(collection.versions())) == 0:
        #     collection.delete()
