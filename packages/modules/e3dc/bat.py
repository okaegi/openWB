#!/usr/bin/env python3
from typing import Dict, Union
import logging

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.modbus import ModbusDataType, Endian
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_bat_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.e3dc.config import E3dcBatSetup


log = logging.getLogger(__name__)


def read_bat(client: modbus.ModbusTcpClient_):
    # 40082 SoC
    soc = client.read_holding_registers(40082, ModbusDataType.INT_16, unit=1)
    # 40069 Speicherleistung
    power = client.read_holding_registers(40069, ModbusDataType.INT_32, wordorder=Endian.Little, unit=1)
    return soc, power


class E3dcBat:
    def __init__(self,
                 device_id: int,
                 ip_address: str,
                 component_config: Union[Dict, E3dcBatSetup]) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(E3dcBatSetup, component_config)
        # bat
        self.__sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.__store = get_bat_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)
        self.__ip_address = ip_address

    def update(self, client: modbus.ModbusTcpClient_) -> None:

        soc, power = read_bat(client)
        log.debug("Ip: %s, soc %d power %d", self.__ip_address,
                  soc, power)
        imported, exported = self.__sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.__store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=E3dcBatSetup)
