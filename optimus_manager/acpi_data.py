# Taken from /usr/share/acpi_call/examples/turn_off_gpu.sh, from the package acpi_call.
# This script only provides commands to turn the GPU off, so I had to guess the corresponding commands
# for turning it on. May or may not be correct.

ACPI_STRINGS = [

    # OFF command, ON command
    ("\\_SB.PCI0.P0P1.VGA._OFF", "\\_SB.PCI0.P0P1.VGA._ON"),
    ("\\_SB.PCI0.P0P2.VGA._OFF", "\\_SB.PCI0.P0P2.VGA._ON"),
    ("\\_SB.PCI0.P0P3.PEGP._OFF", "\\_SB.PCI0.P0P3.PEGP._ON"),
    ("\\_SB.PCI0.P0P2.PEGP._OFF", "\\_SB.PCI0.P0P2.PEGP._ON"),
    ("\\_SB.PCI0.P0P1.PEGP._OFF", "\\_SB.PCI0.P0P1.PEGP._ON"),
    ("\\_SB.PCI0.MXR0.MXM0._OFF", "\\_SB.PCI0.MXR0.MXM0._ON"),
    ("\\_SB.PCI0.PEG1.GFX0._OFF", "\\_SB.PCI0.PEG1.GFX0._ON"),
    ("\\_SB.PCI0.PEG0.GFX0.DOFF", "\\_SB.PCI0.PEG0.GFX0.DON"),
    ("\\_SB.PCI0.PEG1.GFX0.DOFF", "\\_SB.PCI0.PEG1.GFX0.DON"),
    ("\\_SB.PCI0.PEG0.PEGP._OFF", "\\_SB.PCI0.PEG0.PEGP._ON"),
    ("\\_SB.PCI0.XVR0.Z01I.DGOF", "\\_SB.PCI0.XVR0.Z01I.DGON"),
    ("\\_SB.PCI0.PEGR.GFX0._OFF", "\\_SB.PCI0.PEGR.GFX0._ON"),
    ("\\_SB.PCI0.PEG.VID._OFF", "\\_SB.PCI0.PEG.VID._ON"),
    ("\\_SB.PCI0.PEG0.VID._OFF", "\\_SB.PCI0.PEG0.VID._ON"),
    ("\\_SB.PCI0.P0P2.DGPU._OFF", "\\_SB.PCI0.P0P2.DGPU._ON"),
    ("\\_SB.PCI0.P0P4.DGPU.DOFF", "\\_SB.PCI0.P0P4.DGPU.DON"),
    ("\\_SB.PCI0.IXVE.IGPU.DGOF", "\\_SB.PCI0.IXVE.IGPU.DGON"),
    ("\\_SB.PCI0.LPC.EC.PUBS._OFF", "\\_SB.PCI0.LPC.EC.PUBS._ON"),
    ("\\_SB.PCI0.P0P2.NVID._OFF", "\\_SB.PCI0.P0P2.NVID._ON"),
    ("\\_SB_.PCI0.PEGP.DGFX._OFF", "\\_SB_.PCI0.PEGP.DGFX._ON"),
    ("\\_SB.PCI0.GPP0.PG00._OFF", "\\_SB.PCI0.GPP0.PG00._ON"),
    ("\\_SB.PCI0.PEG0.PEGP.SGOF", "\\_SB.PCI0.PEG0.PEGP.SGON"),
    ("\\_SB.PCI0.RP05.PXSX._OFF", "\\_SB.PCI0.RP05.PXSX._ON")
]
