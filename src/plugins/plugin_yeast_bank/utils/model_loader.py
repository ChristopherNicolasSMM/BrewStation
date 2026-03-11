from core.plugin_model_registry import get_prefixed_model

PLUGIN_NAME = "plugin_yeast_bank"

def _get_prefixed_model(model_class_name: str):
    prefixed = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed:
        return prefixed

    # fallback direto
    try:
        from plugins.plugin_yeast_bank.model.yeast_bank_models import (
            YeastStrain, YeastBankItem, YeastStarterLog, YeastCountHistory, YeastBankConfig, YeastStorageDevice, YeastStorageReading
        )
        model_map = {
            "YeastStrain": YeastStrain,
            "YeastBankItem": YeastBankItem,
            "YeastStarterLog": YeastStarterLog,
            "YeastCountHistory": YeastCountHistory,
            "YeastBankConfig": YeastBankConfig,
            "YeastStorageDevice": YeastStorageDevice,
            "YeastStorageReading": YeastStorageReading,
        }
        return model_map.get(model_class_name)
    except Exception:
        return None

def get_yeast_strain():
    return _get_prefixed_model("YeastStrain")

def get_yeast_bank_item():
    return _get_prefixed_model("YeastBankItem")

def get_yeast_starter_log():
    return _get_prefixed_model("YeastStarterLog")

def get_yeast_bank_config():
    return _get_prefixed_model("YeastBankConfig")

def get_yeast_storage_device():
    return _get_prefixed_model("YeastStorageDevice")

def get_yeast_storage_reading():
    return _get_prefixed_model("YeastStorageReading")


def get_yeast_count_history():
    return _get_prefixed_model("YeastCountHistory")
