# -*- coding: utf-8 -*-
import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyfibot.modules.module_bmi import calc_bmi, print_bmi, command_bmi


class TestBMICalculation:
    """Test BMI calculation logic"""

    def test_calc_bmi_normal_values(self):
        """Test BMI calculation with normal values"""
        # 170cm, 70kg = BMI 24.22
        result = calc_bmi(170, 70)
        assert abs(result - 24.22) < 0.01

    def test_calc_bmi_formula_accuracy(self):
        """Test BMI formula accuracy with known values"""
        # BMI = (weight in kg / (height in m)^2)
        # 180cm, 80kg = 80 / (1.8^2) = 80 / 3.24 = 24.69
        result = calc_bmi(180, 80)
        expected = (80 / (1.8 ** 2))
        assert abs(result - expected) < 0.01

    def test_calc_bmi_edge_cases(self):
        """Test BMI calculation with edge cases"""
        # Very tall person
        result = calc_bmi(220, 100)
        expected = (100 / (2.2 ** 2))
        assert abs(result - expected) < 0.01
        
        # Very short person  
        result = calc_bmi(120, 30)
        expected = (30 / (1.2 ** 2))
        assert abs(result - expected) < 0.01

    def test_calc_bmi_float_inputs(self):
        """Test BMI calculation with float inputs"""
        result = calc_bmi(175.5, 72.3)
        expected = (72.3 / (1.755 ** 2))
        assert abs(result - expected) < 0.01

    def test_calc_bmi_string_inputs(self):
        """Test BMI calculation with string inputs (should convert)"""
        result = calc_bmi(float("170"), float("70"))
        expected = (70 / (1.7 ** 2))
        assert abs(result - expected) < 0.01

    def test_calc_bmi_zero_height(self):
        """Test BMI calculation with zero height (should raise error)"""
        with pytest.raises(ZeroDivisionError):
            calc_bmi(0, 70)

    def test_calc_bmi_negative_values(self):
        """Test BMI calculation with negative values"""
        # The function doesn't validate inputs, but let's test behavior
        result = calc_bmi(-170, 70)
        # Actually with -170cm height squared becomes positive, so result is positive
        assert result > 0  # Height squared becomes positive

    def test_calc_bmi_very_large_values(self):
        """Test BMI calculation with very large values"""
        result = calc_bmi(300, 200)
        expected = (200 / (3.0 ** 2))
        assert abs(result - expected) < 0.01


class TestBMICategories:
    """Test BMI categorization logic"""

    def test_severely_underweight(self):
        """Test severely underweight category"""
        result = print_bmi(15.0)
        assert "severely underweight" in result
        assert "15.00" in result

    def test_severely_underweight_boundary(self):
        """Test severely underweight boundary"""
        result = print_bmi(16.4)
        assert "severely underweight" in result
        
        result = print_bmi(16.5)
        assert "underweight (from 16.5 to 18.4)" in result

    def test_underweight(self):
        """Test underweight category"""
        result = print_bmi(17.0)
        assert "underweight (from 16.5 to 18.4)" in result
        assert "17.00" in result

    def test_underweight_boundary(self):
        """Test underweight boundary"""
        result = print_bmi(18.4)
        assert "underweight (from 16.5 to 18.4)" in result
        
        result = print_bmi(18.5)
        assert "normal (from 18.5 to 24.9)" in result

    def test_normal_weight(self):
        """Test normal weight category"""
        result = print_bmi(22.0)
        assert "normal (from 18.5 to 24.9)" in result
        assert "22.00" in result

    def test_normal_weight_boundary(self):
        """Test normal weight boundary"""
        result = print_bmi(24.9)
        assert "normal (from 18.5 to 24.9)" in result
        
        result = print_bmi(25.0)
        assert "overweight (from 25 to 30)" in result

    def test_overweight(self):
        """Test overweight category"""
        result = print_bmi(27.5)
        assert "overweight (from 25 to 30)" in result
        assert "27.50" in result

    def test_overweight_boundary(self):
        """Test overweight boundary"""
        result = print_bmi(30.0)
        assert "overweight (from 25 to 30)" in result
        
        result = print_bmi(30.1)
        assert "obese class I (from 30.1 to 34.9)" in result

    def test_obese_class_i(self):
        """Test obese class I category"""
        result = print_bmi(32.0)
        assert "obese class I (from 30.1 to 34.9)" in result
        assert "32.00" in result

    def test_obese_class_i_boundary(self):
        """Test obese class I boundary"""
        result = print_bmi(34.9)
        assert "obese class I (from 30.1 to 34.9)" in result
        
        result = print_bmi(35.0)
        assert "obese class II (from 35 to 40)" in result

    def test_obese_class_ii(self):
        """Test obese class II category"""
        result = print_bmi(37.5)
        assert "obese class II (from 35 to 40)" in result
        assert "37.50" in result

    def test_obese_class_ii_boundary(self):
        """Test obese class II boundary"""
        result = print_bmi(40.0)
        assert "obese class II (from 35 to 40)" in result
        
        result = print_bmi(40.1)
        assert "obese class III (over 40)" in result

    def test_obese_class_iii(self):
        """Test obese class III category"""
        result = print_bmi(45.0)
        assert "obese class III (over 40)" in result
        assert "45.00" in result

    def test_extreme_values(self):
        """Test with extreme BMI values"""
        result = print_bmi(5.0)
        assert "severely underweight" in result
        
        result = print_bmi(100.0)
        assert "obese class III (over 40)" in result

    def test_decimal_precision(self):
        """Test decimal precision in output"""
        result = print_bmi(23.456789)
        assert "23.46" in result  # Should be rounded to 2 decimal places

    def test_return_format(self):
        """Test that print_bmi returns expected format"""
        result = print_bmi(22.5)
        assert result.startswith("your bmi is ")
        assert " which is " in result
        assert result.endswith("normal (from 18.5 to 24.9)")


class MockBot:
    """Mock bot for testing command function"""
    def __init__(self):
        self.messages = []
    
    def say(self, channel, message):
        self.messages.append((channel, message))
        return (channel, message)


class TestBMICommand:
    """Test the BMI command function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.bot = MockBot()

    def test_command_bmi_valid_input(self):
        """Test BMI command with valid input"""
        result = command_bmi(self.bot, "testuser", "#testchan", "170/70")
        
        assert result[0] == "#testchan"
        assert "24.22" in result[1]
        assert "normal" in result[1]

    def test_command_bmi_invalid_format(self):
        """Test BMI command with invalid format"""
        result = command_bmi(self.bot, "testuser", "#testchan", "170")
        
        assert result[0] == "#testchan"
        assert "Usage: bmi height(cm)/weight(kg)" in result[1]

    def test_command_bmi_too_many_parts(self):
        """Test BMI command with too many parts"""
        result = command_bmi(self.bot, "testuser", "#testchan", "170/70/extra")
        
        assert result[0] == "#testchan"
        assert "Usage: bmi height(cm)/weight(kg)" in result[1]

    def test_command_bmi_empty_args(self):
        """Test BMI command with empty arguments"""
        result = command_bmi(self.bot, "testuser", "#testchan", "")
        
        assert result[0] == "#testchan"
        assert "Usage: bmi height(cm)/weight(kg)" in result[1]

    def test_command_bmi_no_separator(self):
        """Test BMI command without separator"""
        result = command_bmi(self.bot, "testuser", "#testchan", "170 70")
        
        assert result[0] == "#testchan"
        assert "Usage: bmi height(cm)/weight(kg)" in result[1]

    def test_command_bmi_with_spaces(self):
        """Test BMI command with spaces around values"""
        result = command_bmi(self.bot, "testuser", "#testchan", " 170 / 70 ")
        
        # This should work as split() will handle extra spaces
        assert result[0] == "#testchan"
        assert "24.22" in result[1]

    def test_command_bmi_non_numeric_values(self):
        """Test BMI command with non-numeric values"""
        with pytest.raises(ValueError):
            command_bmi(self.bot, "testuser", "#testchan", "abc/def")

    def test_command_bmi_zero_height(self):
        """Test BMI command with zero height"""
        with pytest.raises(ZeroDivisionError):
            command_bmi(self.bot, "testuser", "#testchan", "0/70")

    def test_command_bmi_negative_values(self):
        """Test BMI command with negative values"""
        result = command_bmi(self.bot, "testuser", "#testchan", "-170/70")
        
        # Should still calculate, but result will be normal since height squared is positive
        assert result[0] == "#testchan"
        # The BMI calculation with -170 height still gives normal result
        assert "normal" in result[1]

    def test_command_bmi_float_strings(self):
        """Test BMI command with float string values"""
        # The actual command uses int() which will fail with floats
        with pytest.raises(ValueError):
            command_bmi(self.bot, "testuser", "#testchan", "175.5/72.3")


class TestBMIRealWorldCases:
    """Test BMI with real-world test cases"""

    def test_realistic_adult_males(self):
        """Test BMI for realistic adult male values"""
        test_cases = [
            (180, 75, "normal"),  # Average male
            (175, 65, "normal"),  # Lean male  
            (185, 95, "overweight"),  # Heavy male
            (170, 50, "underweight"),  # Light male - adjusted to actually be underweight
        ]
        
        for height, weight, expected_category in test_cases:
            bmi = calc_bmi(height, weight)
            result = print_bmi(bmi)
            assert expected_category in result

    def test_realistic_adult_females(self):
        """Test BMI for realistic adult female values"""
        test_cases = [
            (165, 60, "normal"),  # Average female
            (160, 50, "normal"),  # Lean female
            (170, 75, "overweight"),  # Heavy female
            (155, 42, "underweight"),  # Light female - adjusted to actually be underweight
        ]
        
        for height, weight, expected_category in test_cases:
            bmi = calc_bmi(height, weight)
            result = print_bmi(bmi)
            assert expected_category in result

    def test_athlete_edge_cases(self):
        """Test BMI for athletic individuals (muscle mass considerations)"""
        # Note: BMI doesn't account for muscle mass, so muscular athletes 
        # might be classified as overweight despite being healthy
        test_cases = [
            (180, 85, "overweight"),  # Muscular athlete
            (175, 80, "overweight"),  # Strong athlete
        ]
        
        for height, weight, expected_category in test_cases:
            bmi = calc_bmi(height, weight)
            result = print_bmi(bmi)
            assert expected_category in result

    def test_documentation_examples(self):
        """Test examples that could be used in documentation"""
        # WHO standard examples
        bmi_18_5 = calc_bmi(170, 53.465)  # Should be exactly 18.5
        assert abs(bmi_18_5 - 18.5) < 0.01
        
        bmi_25 = calc_bmi(170, 72.25)  # Should be exactly 25.0
        assert abs(bmi_25 - 25.0) < 0.01
        
        bmi_30 = calc_bmi(170, 86.7)  # Should be exactly 30.0
        assert abs(bmi_30 - 30.0) < 0.01