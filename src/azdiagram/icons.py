"""Default icons: draw.io's built-in Azure stencils, so diagrams need no embedded images."""

BASE = "img/lib/azure2/"

KIND_ICONS: dict[str, str] = {
    "external_section": "general/Globe.svg",
    "entra_tenant": "identity/Azure_Active_Directory.svg",
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
}

# (kind, variant) overrides, e.g. the `kind` field of an external system or service principal.
VARIANT_ICONS: dict[tuple[str, str], str] = {
    ("external", "system"): "general/Server_Farm.svg",
    ("external", "saas"): "general/Globe.svg",
    ("external", "internet"): "general/Globe.svg",
    ("external", "onPrem"): "networking/On_Premises_Data_Gateways.svg",
    ("external", "user"): "identity/Users.svg",
    ("service_principal", "application"): "identity/Enterprise_Applications.svg",
    ("service_principal", "managedIdentity"): "identity/Managed_Identities.svg",
}


def icon_for(kind: str, variant: str | None = None) -> str:
    """Return the draw.io image path for a node kind, honouring an optional variant."""
    path = (VARIANT_ICONS.get((kind, variant)) if variant else None) or KIND_ICONS.get(kind)
    if path is None:
        raise KeyError(f"no icon for kind {kind!r} (variant {variant!r})")
    return BASE + path


def normalize_icon(icon: str) -> str:
    """draw.io styles are ';'-separated, so data URIs must drop ';base64' (draw.io's own convention)."""
    if icon.startswith("data:") and ";base64," in icon:
        return icon.replace(";base64,", ",", 1)
    return icon
