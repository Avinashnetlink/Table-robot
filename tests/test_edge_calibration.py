import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('calibrate_edges',Path(__file__).resolve().parents[1]/'tools/calibrate_edges.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class CalibrationTests(unittest.TestCase):
    def row(self,mm,valid=True,model='VL6180X'):
        return {'edge_sensor':model,'edge_mm':[mm]*3,'edge_valid':[valid]*3}
    def test_bands(self):
        lo,hi=module.propose([self.row(29),self.row(31)],[self.row(90)])
        self.assertEqual(lo,[24]*3); self.assertEqual(hi,[36]*3)
    def test_air_overlap(self):
        with self.assertRaises(ValueError): module.propose([self.row(30)],[self.row(32)])
    def test_invalid_desk_and_mixed_models(self):
        with self.assertRaises(ValueError): module.propose([self.row(30,False)],[self.row(90)])
        with self.assertRaises(ValueError): module.propose([self.row(30)],[self.row(90,model='VL53L0X')])
    def test_short_range_limit(self):
        with self.assertRaises(ValueError): module.propose([self.row(98)],[self.row(0,False)])
    def test_capture_requires_samples_and_rejects_bus_fault(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'capture.jsonl'
            row=dict(self.row(30),type='status',moving=False,unlocked=False,edge_status=[0]*3)
            path.write_text(json.dumps(row)+'\n')
            with self.assertRaises(ValueError): module.load(path)
            path.write_text((json.dumps(row)+'\n')*20)
            self.assertEqual(len(module.load(path)),20)
            row['edge_status'][1]=250
            path.write_text((json.dumps(row)+'\n')*20)
            with self.assertRaises(ValueError): module.load(path)
    def test_capture_rejects_armed_robot(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'capture.jsonl'
            row=dict(self.row(30),type='status',moving=False,unlocked=True,edge_status=[0]*3)
            path.write_text((json.dumps(row)+'\n')*20)
            with self.assertRaises(ValueError): module.load(path)
