"""Module to deal with rotameric libraries"""

import math
import sys


class RotamerLibrary(object):
    """Interface class"""
    pass


class InterfaceSurfaceLibrary(RotamerLibrary):
    """Rotamers is a dictionary containing for each residue name as a key a list of rotamers,
    each one a dictionary of unbound and bound values for each chi angle.

    Values come from Table S3 (http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3393779) non-redundant rotamer
    libraries for interface surface only.
    """
    rotamers = {"CYS": [{"x1": [-69.8, -66.2]},
                        {"x1": [-179.0, 178.8]},
                        {"x1": [74.9, 62.1]}],
                "SER": [{"x1": [58.1, 62.7]},
                        {"x1": [-61.7, -58.2]},
                        {"x1": [179.3, 177.0]}],
                "THR": [{"x1": [62.5, 55.1]},
                        {"x1": [-59.3, -61.1]},
                        {"x1": [-174.3, -174.0]}],
                "VAL": [{"x1": [173.7, 177.3]},
                        {"x1": [-61.5, -62.2]},
                        {"x1": [70.4, 67.9]}],
                "PRO": [{"x1": [-29.5, -28.5], "x2": [38.1, 40.6]},
                        {"x1": [32.3, 30.2], "x2": [-39.5, -40.8]}],
                "TRP": [{"x1": [-63.2, -71.3], "x2": [93.5, 85.4]},
                        {"x1": [175.1, 177.0], "x2": [-107.1, -108.0]},
                        {"x1": [-68.2, -51.3], "x2": [-25.0, -22.7]},
                        {"x1": [-75.8, -61.7], "x2": [-96.4, -84.8]},
                        {"x1": [61.4, 62.4], "x2": [94.2, 85.2]},
                        {"x1": [-176.2, -177.7], "x2": [69.2, 69.5]},
                        {"x1": [54.6, 55.7], "x2": [-93.0, -93.3]}],
                "ASP": [{"x1": [-70.5, -62.3], "x2": [-26.3, -33.9]},
                        {"x1": [-166.4, -174.7], "x2": [14.5, 11.6]},
                        {"x1": [61.2, 63.3], "x2": [0.9, 10.3]}],
                "PHE": [{"x1": [-58.8, -61.3], "x2": [105.0, 86.3]},
                        {"x1": [177.6, 177.0], "x2": [76.4, 77.4]},
                        {"x1": [51.6, 60.4], "x2": [76.8, 81.8]}],
                "HIS": [{"x1": [-71.1, -54.8], "x2": [85.6, -79.6]},
                        {"x1": [78.4, 72.0], "x2": [-101.0, -93.2]},
                        {"x1": [-174.6, -174.5], "x2": [80.9, 91.6]}],
                "ILE": [{"x1": [-63.1, -62.3], "x2": [171.4, 174.9]},
                        {"x1": [64.2, 57.8], "x2": [169.7, 169.8]},
                        {"x1": [-168.1, 179.6], "x2": [167.8, 169.7]}],
                "LEU": [{"x1": [-63.4, -67.7], "x2": [175.9, 174.3]},
                        {"x1": [179.8, -179.5], "x2": [57.6, 61.8]},
                        {"x1": [100.6, 45.2], "x2": [121.9, 86.1]}],
                "ASN": [{"x1": [-66.5, -68.9], "x2": [-50.2, -37.3]},
                        {"x1": [-177.5, -178.8], "x2": [66.9, 42.8]},
                        {"x1": [61.5, 64.0], "x2": [21.8, 24.6]}],
                "TYR": [{"x1": [-65.0, -69.2], "x2": [88.8, 88.2]},
                        {"x1": [-174.3, -179.7], "x2": [70.8, 74.8]},
                        {"x1": [61.2, 61.5], "x2": [93.5, 94.7]}],
                "GLU": [{"x1": [-62.1, -62.9], "x2": [-178.4, 177.9], "x3": [-14.1, 3.5]},
                        {"x1": [-177.8, 178.2], "x2": [177.1, 174.7], "x3": [-7.9, -13.8]},
                        {"x1": [-58.9, -70.2], "x2": [-69.2, -64.9], "x3": [-46.8, -76.7]},
                        {"x1": [-175.5, -177.9], "x2": [56.6, 55.6], "x3": [45.9, 30.1]},
                        {"x1": [70.7, 65.7], "x2": [-174.0, -177.7], "x3": [18.6, 18.6]},
                        {"x1": [-58.4, -72.5], "x2": [48.0, 76.1], "x3": [62.2, 23.5]},
                        {"x1": [68.7, 70.2], "x2": [-94.0, -85.2], "x3": [28.0, 39.1]}],
                "GLN": [{"x1": [-62.4, -60.4], "x2": [-175.8, -169.9], "x3": [57.7, -56.6]},
                        {"x1": [-65.1, -59.5], "x2": [-52.3, -58.3], "x3": [-47.9, 57.9]},
                        {"x1": [-174.0, -169.0], "x2": [-177.2, -174.8], "x3": [-47.9, 57.9]},
                        {"x1": [-158.3, -161.4], "x2": [58.8, 57.6], "x3": [68.6, 53.0]},
                        {"x1": [75.9, 44.8], "x2": [176.7, 169.2], "x3": [75.6, -68.6]},
                        {"x1": [-76.1, -83.4], "x2": [77.8, 79.5], "x3": [7.9, 23.0]}],
                "MET": [{"x1": [-79.8, -52.7], "x2": [-52.6, -69.5], "x3": [-97.0, -92.0]},
                        {"x1": [-71.4, -67.0], "x2": [172.1, 179.7], "x3": [-55.2, 79.5]},
                        {"x1": [-161.5, -121.3], "x2": [165.1, -174.6], "x3": [87.7, -56.0]},
                        {"x1": [53.8, 53.8], "x2": [-148.2, -148.2], "x3": [17.0, 17.0]}],
                "ARG": [{"x1": [-72.0, -69.9], "x2": [178.5, 167.0], "x3": [177.0, 171.6], "x4": [-176.7, -173.0]},
                        {"x1": [-72.1, -61.6], "x2": [140.9, -158.9], "x3": [-174.1, 179.6], "x4": [86.7, 84.2]},
                        {"x1": [-163.8, 158.3], "x2": [-144.6, 166.9], "x3": [-37.4, -30.3], "x4": [162.7, 171.8]},
                        {"x1": [-174.7, -174.4], "x2": [161.7, 174.4], "x3": [-165.9, -178.6], "x4": [173.1, 177.3]},
                        {"x1": [-56.9, -60.4], "x2": [-164.2, -166.7], "x3": [-58.3, -61.5], "x4": [-81.6, 174.9]},
                        {"x1": [-62.4, -60.2], "x2": [-57.9, -69.4], "x3": [-172.6, -168.0], "x4": [-174.5, -174.7]},
                        {"x1": [176.8, 71.1], "x2": [73.5, 176.7], "x3": [-168.3, 177.8], "x4": [-175.0, -75.7]},
                        {"x1": [-171.0, 178.3], "x2": [-173.3, 176.6], "x3": [-57.2, -70.2], "x4": [-81.9, -79.0]},
                        {"x1": [55.0, 81.8], "x2": [-173.0, 167.6], "x3": [175.6, 164.9], "x4": [98.1, 80.0]},
                        {"x1": [55.7, 64.1], "x2": [157.6, -176.5], "x3": [-74.9, -69.5], "x4": [178.3, 156.0]},
                        {"x1": [-31.2, -31.2], "x2": [-164.8, -164.8], "x3": [69.6, 69.6], "x4": [64.2, 64.2]}],
                "LYS": [{"x1": [-69.3, -66.5], "x2": [-179.7, 178.8], "x3": [179.2, 179.6], "x4": [-180.0, 177.2]},
                        {"x1": [-173.2, -175.5], "x2": [179.9, -179.1], "x3": [179.7, 175.5], "x4": [-176.8, -174.4]},
                        {"x1": [-62.3, -60.0], "x2": [-64.5, -59.1], "x3": [175.8, -179.7], "x4": [174.5, 179.9]},
                        {"x1": [66.8, 62.2], "x2": [-179.2, -179.6], "x3": [180.0, -179.3], "x4": [173.3, 177.1]},
                        {"x1": [-178.7, -159.4], "x2": [58.2, 75.8], "x3": [-175.3, 179.0], "x4": [173.2, 177.7]}]
                }

    @staticmethod
    def get_closest_rotamer(residue, chi_angles):
        """Calculates the closest rotamer to the given residue"""
        if not chi_angles['x1']:
            return None, None
        minim_rmsd = sys.maxint
        minim_rotamer = 0
        for index, rotamer in enumerate(InterfaceSurfaceLibrary.rotamers[residue.name]):
            rmsd = 0.
            for chi, values in rotamer.iteritems():
                rmsd += (values[0] - chi_angles[chi])**2
            rmsd = math.sqrt(rmsd)
            if rmsd < minim_rmsd:
                minim_rotamer = index
                minim_rmsd = rmsd
        return minim_rotamer, InterfaceSurfaceLibrary.rotamers[residue.name][minim_rotamer]


class TransitionMap(object):
    """Interface transition map"""
    cys = [[50.0, 5.9, 2.9],
           [2.9, 20.6, 2.9],
           [0.0, 0.0, 14.7]]
    ser = [[28.8, 7.5, 5.6],
           [11.1, 17.3, 3.6],
           [5.6, 6.9, 10.1]]
    thr = [[39.5, 8.8, 2.4],
           [9.5, 25.9, 1.4],
           [2.4, 2.0, 3.7]]
    val = [[59.5, 6.3, 2.7],
           [5.5, 13.4, 1.6],
           [3.3, 1.8, 4.7]]
    pro = [[38.3, 14.5],
           [14.5, 32.6]]
    asp = [[43.6, 5.5, 2.8],
           [7.1, 19.3, 2.1],
           [3.7, 1.5, 14.1]]
    phe = [[40.6, 4.7, 0.9],
           [1.9, 32.1, 0.0],
           [4.7, 1.9, 9.4]]
    his = [[46.5, 3.9, 7.0],
           [3.1, 14.7, 0.8],
           [3.9, 3.9, 14.7]]
    ile = [[68.3, 3.2, 4.0],
           [6.3, 5.6, 1.6],
           [2.4, 2.4, 5.6]]
    leu = [[59.6, 7.7, 0.9],
           [10.6, 16.6, 0.4],
           [1.7, 0.4, 0.9]]
    asn = [[47.6, 7.5, 0.7],
           [11.2, 18.7, 0.7],
           [2.6, 1.5, 4.5]]
    trp = [[31.9, 1.4, 2.9, 0.0, 1.4, 0.0, 1.4],
           [1.4, 10.1, 0.0, 0.0, 0.0, 0.0, 0.0],
           [4.3, 0.0, 5.8, 0.0, 0.0, 0.0, 2.9],
           [4.3, 1.4, 1.4, 2.9, 0.0, 0.0, 0.0],
           [0.0, 0.0, 0.0, 1.4, 2.9, 0.0, 1.4],
           [0.0, 0.0, 0.0, 0.0, 0.0, 7.2, 0.0],
           [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.7]]
    tyr = [[49.5, 3.3, 1.1],
           [6.0, 27.7, 2.2],
           [1.1, 0.5, 7.6]]
    met = [[10.8, 2.7, 1.4],
           [2.7, 12.2, 2.7],
           [1.4, 1.4, 1.4],
           [1.4, 1.4, 0.0]]
    glu = [[17.7, 6.1, 3.9, 0.5, 1.0, 0.7, 0.2],
           [4.6, 13.1, 1.9, 0.7, 1.2, 1.2, 1.0],
           [2.4, 1.2, 5.6, 0.0, 0.7, 0.5, 0.2],
           [1.0, 2.2, 0.5, 1.0, 0.5, 0.0, 0.0],
           [2.9, 0.7, 0.2, 0.2, 1.5, 0.7, 0.0],
           [1.0, 0.2, 0.0, 0.5, 0.2, 1.5, 0.2],
           [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5]]
    gln = [[19.3, 5.4, 1.2, 1.5, 1.2, 0.4],
           [3.9, 7.7, 1.9, 1.2, 0.8, 0.4],
           [1.5, 0.0, 9.3, 0.4, 0.0, 0.0],
           [1.5, 1.2, 0.8, 2.3, 0.0, 0.4],
           [0.8, 0.8, 0.4, 0.0, 0.8, 0.0],
           [2.3, 0.0, 0.0, 0.4, 0.0, 1.5]]
    lys = [[19.8, 2.7, 2.5, 1.0],
           [7.2, 9.9, 2.2, 0.7, 0.5],
           [3.2, 0.5, 3.2, 1.2, 0.2],
           [1.0, 0.7, 0.2, 1.7, 0.0],
           [1.2, 2.2, 0.2, 0.0, 0.2]]
    arg = [[5.8, 1.2, 1.4, 2.6, 2.6, 0.9, 1.2, 0.3, 0.3, 0.0],
           [1.4, 0.9, 0.3, 0.9, 0.3, 0.0, 0.0, 0.3, 0.0, 0.3],
           [0.9, 0.6, 3.5, 1.7, 1.2, 0.6, 0.0, 0.0, 0.3, 0.0],
           [2.3, 0.6, 1.4, 4.6, 0.3, 0.6, 0.0, 0.6, 0.3, 0.6],
           [1.4, 0.0, 0.0, 0.9, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0],
           [0.6, 0.3, 0.3, 0.6, 0.6, 1.7, 0.0, 0.0, 0.0, 0.0],
           [0.0, 0.0, 1.2, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
           [0.3, 0.0, 0.3, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
           [0.0, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.3, 0.3, 0.0],
           [0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.0, 0.6],
           [0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
           [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
