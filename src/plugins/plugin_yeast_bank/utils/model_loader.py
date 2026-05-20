from core.plugin_model_registry import get_prefixed_model

PLUGIN_NAME = "plugin_yeast_bank"


def _get_prefixed_model(model_class_name: str):
    prefixed = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed:
        return prefixed

    try:
        from plugins.plugin_yeast_bank.model.yeast_bank_models import (
            YeastBankConfig, YeastBankEvent, YeastBankItem,
            YeastCellCountHistory, YeastStarterLog, YeastStorageDevice,
            YeastStorageReading, YeastStrain)
        model_map = {
            "YeastStrain": YeastStrain,
            "YeastBankItem": YeastBankItem,
            "YeastStarterLog": YeastStarterLog,
            "YeastBankConfig": YeastBankConfig,
            "YeastStorageDevice": YeastStorageDevice,
            "YeastStorageReading": YeastStorageReading,
            "YeastCellCountHistory": YeastCellCountHistory,
            "YeastBankEvent": YeastBankEvent,
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


def get_yeast_cell_count_history():
    return _get_prefixed_model("YeastCellCountHistory")


def get_yeast_bank_event():
    return _get_prefixed_model("YeastBankEvent")
