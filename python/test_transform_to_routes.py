#!/usr/bin/env python3

import re
import unittest

import transform_to_routes as trans

"""
Unit tests for test_transform_to_routes.py

Run like this:
    python3 -m unittest test_transform_to_routes.py
    or
    ./test_transform_to_routes.py
"""

class Test_Transform_to_routes(unittest.TestCase):
  def test_basics(self):
      """
      Test basic run use case for both modes.
      """
      for aMode in trans.mode_list:
          self.assertEqual(trans.transform_to_routes("sampleStatFile.txt", "192.168.1.1", aMode)[0], 0)

  def test_gateway(self):
      """
      Test that the given GW shows up in the routes for both modes.
      """
      anIP = "192.168.1.100"

      for aMode in trans.mode_list:

          tup = trans.transform_to_routes("sampleStatFile.txt", anIP, aMode)
    
          for line in tup[1]:
              if anIP in line:
                  break
          else:
              print(f"The GW of '{anIP}' is not in the '{aMode}' route commands")
              self.assertTrue(False)

          self.assertEqual(tup[0], 0)

  def test_32_bit_linux(self):
      """
      Test that we handle 32 bit networks using correct syntax.
      The sample file contains two 32 bit networks and should look like:
        route add -host x.x.x.x x.x.x.x
      """
      tup = trans.transform_to_routes("sampleStatFile.txt", "192.168.1.131", "linux")
      host_lines = [line for line in tup[1] if re.search("route add -host \d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}", line)]
      self.assertEqual(tup[0], 0)
      self.assertEqual(len(host_lines), 2)

  def test_32_bit_macOS(self):
      """
      Test that we handle 32 bit networks using correct syntax.
      The sample file contains two 32 bit networks and should look like:
        route -n add x.x.x.x/32 x.x.x.x
      """
      tup = trans.transform_to_routes("sampleStatFile.txt", "192.168.1.131", "macOS")
      host_lines = [line for line in tup[1] if re.search("route -n add \d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}/32", line)]
      self.assertEqual(tup[0], 0)
      self.assertEqual(len(host_lines), 2)

if __name__ == '__main__':
    unittest.main()
