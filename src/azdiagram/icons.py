"""Default icons: draw.io's built-in Azure stencils, so diagrams need no embedded images."""

BASE = "img/lib/azure2/"

# draw.io has no current Microsoft 365 icons, so those come from Microsoft's Fluent product icon CDN (pinned build).
M365_BASE = "https://res.cdn.office.net/files/fabric-cdn-prod_20241209.001/assets/brand-icons/product/svg/"

KIND_ICONS = {
    "external_section": "general/Globe.svg",
    "entra_tenant": "identity/Azure_Active_Directory.svg",
    "graph": "web/API_Center.svg",
    "user": "identity/Users.svg",
    "group": "identity/Groups.svg",
    "owners": "identity/Groups.svg",
    "members": "identity/Groups.svg",
    "management_group": "general/Management_Groups.svg",
    "subscription": "general/Subscriptions.svg",
    "resource_group": "general/Resource_Groups.svg",
    "key_vault": "security/Key_Vaults.svg",
    "container_app": "other/Worker_Container_App.svg",
    "container": "containers/Container_Instances.svg",
    "container_registry": "containers/Container_Registries.svg",
    "repository": "general/Image.svg",
    "storage_account": "storage/Storage_Accounts.svg",
    "blob_containers": "general/Blob_Block.svg",
    "blob_container": "general/Storage_Container.svg",
    "foundry": "ai_machine_learning/AI_Foundry.svg",
    "models": "general/Cubes.svg",
    "model_deployment": "ai_machine_learning/Azure_OpenAI.svg",
    "agents": "ai_machine_learning/Bot_Services.svg",
    "agent": "ai_machine_learning/Bot_Services.svg",
    "connectors": "networking/Connections.svg",
    "connector": "integration/Logic_Apps_Custom_Connector.svg",
    "postgres_server": "databases/Azure_Database_PostgreSQL_Server.svg",
    "postgres_database": "databases/Managed_Database.svg",
    "m365": M365_BASE + "m365_48x1.svg",
    "m365_app": M365_BASE + "office_48x1.svg",
}

# (kind, variant) overrides, e.g. the `kind` field of an external system or service principal.
VARIANT_ICONS = {
    ("external", "system"): "general/Server_Farm.svg",
    ("external", "saas"): "general/Globe.svg",
    ("external", "internet"): "general/Globe.svg",
    ("external", "onPrem"): "networking/On_Premises_Data_Gateways.svg",
    ("external", "user"): "identity/Users.svg",
    ("service_principal", "application"): "identity/Enterprise_Applications.svg",
    ("service_principal", "managedIdentity"): "identity/Managed_Identities.svg",
    # HorizonDB has no icon of its own, so it keeps the default PostgreSQL server icon.
    ("postgres_server", "flexibleServer"): "databases/Azure_Database_PostgreSQL_Server.svg",
    ("postgres_server", "cosmosDb"): "databases/Azure_Database_PostgreSQL_Server_Group.svg",
    ("postgres_server", "singleServer"): "img/lib/mscae/Azure_Database_for_PostgreSQL_servers.svg",
    # The CDN has no Exchange icon; Outlook's is the closest match.
    **{
        ("m365_app", app): f"{M365_BASE}{icon}_48x1.svg"
        for app, icon in {
            "exchange": "outlook",
            "sharePoint": "sharepoint",
            "oneDrive": "onedrive",
            "teams": "teams",
            "outlook": "outlook",
            "word": "word",
            "excel": "excel",
            "powerPoint": "powerpoint",
            "oneNote": "onenote",
            "forms": "forms",
            "loop": "loop",
            "copilot": "copilot",
            "stream": "stream",
            "toDo": "todo",
            "project": "project",
            "visio": "visio",
            "sway": "sway",
        }.items()
    },
}


def icon_for(kind: str, variant: str | None = None) -> str:
    path = VARIANT_ICONS.get((kind, variant)) or KIND_ICONS.get(kind)
    if path is None:
        raise KeyError(f"no icon for kind {kind!r} (variant {variant!r})")
    # Paths outside azure2 (e.g. the older mscae set, or a URL) are given in full.
    return path if path.startswith(("img/", "https://")) else BASE + path


def normalize_icon(icon: str) -> str:
    """draw.io styles are ';'-separated, so data URIs must drop ';base64' (draw.io's own convention)."""
    if icon.startswith("data:") and ";base64," in icon:
        return icon.replace(";base64,", ",", 1)
    return icon
