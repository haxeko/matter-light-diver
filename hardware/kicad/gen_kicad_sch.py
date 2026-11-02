#!/usr/bin/env python3
"""
gen_kicad_sch.py - Sinh schematic KiCad 7 (matter_cct_driver.kicad_sch) tu design_db.py.

Kieu "schematic ket noi": moi linh kien la mot symbol, moi chan co net duoc gan nhan toan cuc (global label)
ngay tai dau chan -> ERC/netlist dung, dung de doi chieu voi PCB. So do nguyen ly de doc nam o
hardware/schematics/*.svg. Symbol thu dong lay tu thu vien KiCad; IC dung symbol tu sinh (lib/driver.kicad_sym).
"""
import copy
import os
import sys
import uuid

from kiutils.schematic import Schematic
from kiutils.symbol import Symbol, SymbolLib, SymbolPin
from kiutils.items.common import Position, Property, Effects, Font, PageSettings
from kiutils.items.schitems import (SchematicSymbol, GlobalLabel, HierarchicalSheetInstance,
                                    SymbolProjectInstance, SymbolProjectPath)
from kiutils.items.syitems import SyRect

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design_db as db  # noqa: E402

KICAD_SYM = "/usr/share/kicad/symbols"
OUT_SCH = os.path.join(HERE, "matter_cct_driver.kicad_sch")
OUT_LIB = os.path.join(HERE, "lib", "driver.kicad_sym")
PROJECT = "matter_cct_driver"

# ------------------------------------------------------------ symbol thu vien cho tung linh kien
# ref prefix / fp key -> (lib, symbol)  ; None -> symbol tu sinh (hop chu nhat)
def lib_symbol_for(c):
    ref, fp = c["ref"], c["fp"]
    if ref.startswith("R") and not ref.startswith("RT") and not ref.startswith("RV"):
        return ("Device", "R")
    if ref.startswith("RT"):
        return ("Device", "Thermistor_NTC")
    if ref.startswith("RV"):
        return ("Device", "Varistor")
    if ref.startswith("CY") or ref.startswith("CX"):
        return ("Device", "C")
    if ref.startswith("C"):
        return ("Device", "C_Polarized") if ("CP_" in fp or ref in ("C1", "C27", "C4")) else ("Device", "C")
    if ref.startswith("TVS"):
        return ("Device", "D_TVS")
    if ref == "D10":
        return ("Device", "LED")
    if ref in ("D6", "D7"):
        return ("Device", "D_Schottky")
    if ref.startswith("D"):
        return ("Device", "D")
    if ref == "L1":
        return ("Device", "L_Coupled")          # cuon loc common-mode UU9.8: 4 chan (1-2 cuon L, 3-4 cuon N)
    if ref.startswith("L"):
        return ("Device", "L")
    if ref.startswith("F"):
        return ("Device", "Fuse")
    if ref.startswith("Q"):
        return ("Device", "Q_NMOS_GDS")
    if ref == "U2":
        return ("Isolator", "PC817")
    if ref == "U4":
        return ("Reference_Voltage", "TL431DBZ")
    if ref == "SW1":
        return ("Switch", "SW_DIP_x03")
    if ref == "SW4":
        return ("Switch", "SW_Push")            # SKQG: 4 pad nhung chi 2 so chan (1, 2)
    if ref == "J1":
        return ("Connector_Generic", "Conn_01x02")
    if ref in ("J2", "J4"):
        return ("Connector_Generic", "Conn_01x03")
    if ref == "J3":
        return ("Connector_Generic", "Conn_01x04")
    return None


# IC symbol tu sinh: ten -> (pins trai [(so, ten)], pins phai [(so, ten)])
CUSTOM = {
    "U1": ("UCC28740", [("7", "HV"), ("1", "VDD"), ("2", "VS"), ("3", "FB")], [("6", "DRV"), ("5", "CS"), ("4", "GND"), ("8", "NC")]),
    "U3": ("TLV9002", [("3", "IN1+"), ("2", "IN1-"), ("5", "IN2+"), ("6", "IN2-")], [("1", "OUT1"), ("7", "OUT2"), ("8", "V+"), ("4", "V-")]),
    "U5": ("74AHCT1G125", [("2", "A"), ("1", "~{OE}")], [("4", "Y"), ("5", "VCC"), ("3", "GND")]),
    "U6": ("74AHCT1G125", [("2", "A"), ("1", "~{OE}")], [("4", "Y"), ("5", "VCC"), ("3", "GND")]),
    "U7": ("LMR16006Y", [("2", "VIN"), ("3", "EN"), ("4", "FB")], [("6", "BOOT"), ("5", "SW"), ("1", "GND")]),
    "U8": ("ME6211C33", [("1", "VIN"), ("3", "EN")], [("5", "VOUT"), ("2", "GND"), ("4", "NC")]),
    "T1": ("Transformer_PQ20-20", [("1", "P1 (HV)"), ("2", "P2 nc"), ("3", "P3 (DRAIN)"), ("4", "AUX"), ("5", "AUX_GND")],
           [("6", "SEC+"), ("7", "SEC+"), ("8", "nc"), ("9", "SEC-"), ("10", "SEC-")]),
    "U9": ("ESP32-C6-MINI-1", [("3", "3V3"), ("8", "EN"), ("12", "IO0"), ("13", "IO1"), ("5", "IO2"), ("6", "IO3"), ("9", "IO4"), ("15", "IO6"), ("16", "IO7")],
           [("23", "IO9"), ("17", "IO12"), ("18", "IO13"), ("31", "TXD0"), ("30", "RXD0"), ("24", "IO18"), ("25", "IO19"), ("26", "IO20"), ("1", "GND")],
           {"1": [str(n) for n in db.ESP_GND_PINS if n != 1]}),   # chan GND xep chong len chan 1
}


def make_ic_symbol(name, left, right, stacked=None):
    """symbol hop chu nhat, chan trai/phai, pitch 2.54 mm (don vi mm, truc y huong len).
    stacked: {so_chan_goc: [cac so chan khac]} -> chan an, cung ten/vi tri voi chan goc (GND nhieu chan)."""
    n = max(len(left), len(right))
    h = (n + 1) * 2.54
    w = 15.24
    sym = Symbol(entryName=name)
    sym.inBom = True
    sym.onBoard = True
    sym.properties = [
        Property(key="Reference", value="U", position=Position(0, h / 2 + 1.27, 0)),
        Property(key="Value", value=name, position=Position(0, -h / 2 - 1.27, 0)),
        Property(key="Footprint", value="", position=Position(0, 0, 0), effects=Effects(hide=True)),
        Property(key="Datasheet", value="", position=Position(0, 0, 0), effects=Effects(hide=True)),
    ]
    unit = Symbol(entryName=name, unitId=0, styleId=1)
    unit.graphicItems.append(SyRect(start=Position(-w / 2, h / 2), end=Position(w / 2, -h / 2)))
    pins_unit = Symbol(entryName=name, unitId=1, styleId=1)
    for i, (num, pname) in enumerate(left):
        y = h / 2 - (i + 1) * 2.54
        pins_unit.pins.append(SymbolPin(electricalType="passive", graphicalStyle="line", position=Position(-w / 2 - 5.08, y, 0), length=5.08, name=pname, number=num))
    for i, (num, pname) in enumerate(right):
        y = h / 2 - (i + 1) * 2.54
        pins_unit.pins.append(SymbolPin(electricalType="passive", graphicalStyle="line", position=Position(w / 2 + 5.08, y, 180), length=5.08, name=pname, number=num))
    for anchor, others in (stacked or {}).items():
        base = next(p for p in pins_unit.pins if p.number == anchor)
        for num in others:
            p = copy.deepcopy(base)
            p.number = num
            p.hide = True
            pins_unit.pins.append(p)
    sym.units = [unit, pins_unit]
    return sym


def load_lib_symbol(lib, name, cache={}):
    key = (lib, name)
    if key not in cache:
        sl = SymbolLib().from_file(os.path.join(KICAD_SYM, lib + ".kicad_sym"))
        cache[(lib, None)] = sl
        for s in sl.symbols:
            cache[(lib, s.entryName)] = s
    sym = cache[key]
    # neu symbol "extends" symbol khac -> lay symbol goc
    if sym.extends:
        base = cache.get((lib, sym.extends))
        if base is not None:
            import copy
            b = copy.deepcopy(base)
            b.entryName = sym.entryName
            for u in b.units:
                u.entryName = sym.entryName
            return b
    return sym


def pin_endpoints(sym):
    """tra ve {so_chan: (x, y, angle)} toa do lib (y len) cua DAU chan (noi noi day)"""
    out = {}
    for p in sym.pins:
        out[p.number] = (p.position.X, p.position.Y, p.position.angle)
    for u in sym.units:
        for p in u.pins:
            out[p.number] = (p.position.X, p.position.Y, p.position.angle)
    return out


def main():
    sch = Schematic.create_new()
    sch.version = 20230121
    sch.generator = "gen_kicad_sch"
    sch.uuid = str(uuid.uuid4())
    sch.sheetInstances = [HierarchicalSheetInstance(instancePath="/", page="1")]
    sch.paper = PageSettings(paperSize="A3")
    custom_lib = SymbolLib()
    custom_lib.version = "20220914"
    custom_lib.generator = "gen_kicad_sch"
    lib_syms = {}

    # ---- bo tri: moi khoi mot hang, cac symbol cach nhau
    blocks = {}
    for c in db.C:
        blocks.setdefault(c["block"], []).append(c)
    x0, y0 = 30.0, 30.0
    col_w, row_h = 50.0, 60.0
    for b, items in sorted(blocks.items()):
        y = y0 + (b - 1) * row_h
        for k, c in enumerate(items):
            x = x0 + k * col_w if k < 8 else x0 + (k - 8) * col_w
            yy = y if k < 8 else y + 28.0
            ls = lib_symbol_for(c)
            if ls is None:
                name, left, right, *stacked = CUSTOM[c["ref"]]
                if ("driver", name) not in lib_syms:
                    sym = make_ic_symbol(name, left, right, stacked[0] if stacked else None)
                    custom_lib.symbols.append(copy.deepcopy(sym))
                    lib_syms[("driver", name)] = sym
                sym = lib_syms[("driver", name)]
                lib_id = "driver:" + name
            else:
                if ls not in lib_syms:
                    sym = load_lib_symbol(*ls)
                    lib_syms[ls] = sym
                sym = lib_syms[ls]
                lib_id = ls[0] + ":" + ls[1]
            libnick, entry = lib_id.split(":")
            if lib_id not in [s_.libraryNickname + ":" + s_.entryName for s_ in sch.libSymbols]:
                import copy
                s2 = copy.deepcopy(sym)
                s2.libraryNickname = libnick
                s2.entryName = entry
                for u in s2.units:
                    u.libraryNickname = None
                    u.entryName = entry
                sch.libSymbols.append(s2)
            inst = SchematicSymbol()
            inst.libraryNickname = libnick
            inst.entryName = entry
            inst.position = Position(x, yy, 0)
            inst.uuid = str(uuid.uuid4())
            inst.inBom = True
            inst.onBoard = True
            inst.unit = 1
            # instance data (KiCad 7): ghi reference theo project de khong bi bao "annotation errors"
            inst.instances = [SymbolProjectInstance(name=PROJECT, paths=[
                SymbolProjectPath(sheetInstancePath="/" + sch.uuid, reference=c["ref"], unit=1)])]
            inst.properties = [
                Property(key="Reference", value=c["ref"], position=Position(x, yy - 8, 0)),
                Property(key="Value", value=c["value"], position=Position(x, yy + 8, 0)),
                Property(key="Footprint", value=c["fp"], position=Position(x, yy, 0), effects=Effects(hide=True)),
                Property(key="Datasheet", value="~", position=Position(x, yy, 0), effects=Effects(hide=True)),
            ]
            ends = pin_endpoints(sym)
            placed = set()
            for num, net in c["pins"].items():
                if net == "NC" or num not in ends:
                    continue
                px, py, ang = ends[num]
                gx, gy = x + px, yy - py                    # lib y len -> schematic y xuong
                if (gx, gy) in placed:                      # chan xep chong -> 1 nhan la du
                    continue
                placed.add((gx, gy))
                lbl = GlobalLabel(text=net, position=Position(gx, gy, (ang + 180) % 360), shape="bidirectional")
                lbl.uuid = str(uuid.uuid4())
                lbl.effects = Effects(font=Font(height=1.27, width=1.27))
                sch.globalLabels.append(lbl)
            sch.schematicSymbols.append(inst)
    custom_lib.to_file(OUT_LIB)
    sch.to_file(OUT_SCH)
    print("saved", OUT_SCH, "symbols:", len(sch.schematicSymbols), "labels:", len(sch.globalLabels), "custom:", len(custom_lib.symbols))


if __name__ == "__main__":
    main()
