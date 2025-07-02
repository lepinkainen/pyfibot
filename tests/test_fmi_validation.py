# -*- coding: utf-8 -*-
import pytest
import sys
import os
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from pyfibot.modules.module_fmi import WeatherData, WAWA
    FMI_AVAILABLE = True
except ImportError:
    # Skip tests if dependencies are not available
    FMI_AVAILABLE = False
    pytestmark = pytest.mark.skip("FMI module dependencies not available")


@pytest.mark.skipif(not FMI_AVAILABLE, reason="FMI module dependencies not available")
class TestWeatherDataValidation:
    """Test WeatherData Pydantic model validation"""

    def test_valid_weather_data(self):
        """Test creation with valid data"""
        data = WeatherData(
            place="Helsinki",
            temperature=20.5,
            feels_like=22.0,
            wind_speed=3.5,
            humidity=65,
            cloudiness=4,
            weather_description="clear sky"
        )
        
        assert data.place == "Helsinki"
        assert data.temperature == 20.5
        assert data.feels_like == 22.0
        assert data.wind_speed == 3.5
        assert data.humidity == 65
        assert data.cloudiness == 4
        assert data.weather_description == "clear sky"

    def test_minimal_valid_data(self):
        """Test creation with only required field"""
        data = WeatherData(place="Tampere")
        
        assert data.place == "Tampere"
        assert data.temperature is None
        assert data.feels_like is None
        assert data.wind_speed is None
        assert data.humidity is None
        assert data.cloudiness is None
        assert data.weather_description is None

    def test_missing_place_field(self):
        """Test that place field is required"""
        with pytest.raises(ValueError):
            WeatherData()

    def test_humidity_percentage_validation_valid(self):
        """Test humidity validation with valid values"""
        # Valid humidity values
        data = WeatherData(place="Test", humidity=0)
        assert data.humidity == 0
        
        data = WeatherData(place="Test", humidity=50)
        assert data.humidity == 50
        
        data = WeatherData(place="Test", humidity=100)
        assert data.humidity == 100

    def test_humidity_percentage_validation_invalid(self):
        """Test humidity validation with invalid values"""
        # Invalid humidity values should be set to None
        data = WeatherData(place="Test", humidity=150)
        assert data.humidity is None
        
        data = WeatherData(place="Test", humidity=-10)
        assert data.humidity is None

    def test_cloudiness_validation_valid(self):
        """Test cloudiness validation with valid values"""
        # Valid cloudiness values (0-8 scale)
        for cloudiness in range(0, 9):
            data = WeatherData(place="Test", cloudiness=cloudiness)
            assert data.cloudiness == cloudiness

    def test_cloudiness_validation_invalid(self):
        """Test cloudiness validation with invalid values"""
        # Invalid cloudiness values should be set to None
        data = WeatherData(place="Test", cloudiness=150)
        assert data.cloudiness is None
        
        data = WeatherData(place="Test", cloudiness=-1)
        assert data.cloudiness is None

    def test_temperature_edge_cases(self):
        """Test temperature with various edge cases"""
        # Very cold temperature
        data = WeatherData(place="Antarctica", temperature=-89.2)
        assert data.temperature == -89.2
        
        # Very hot temperature
        data = WeatherData(place="Death Valley", temperature=56.7)
        assert data.temperature == 56.7
        
        # Zero temperature
        data = WeatherData(place="Freezing Point", temperature=0.0)
        assert data.temperature == 0.0
        
        # Float precision
        data = WeatherData(place="Precise", temperature=20.123456)
        assert data.temperature == 20.123456

    def test_wind_speed_edge_cases(self):
        """Test wind speed with various edge cases"""
        # No wind
        data = WeatherData(place="Calm", wind_speed=0.0)
        assert data.wind_speed == 0.0
        
        # Strong wind
        data = WeatherData(place="Hurricane", wind_speed=50.0)
        assert data.wind_speed == 50.0
        
        # Very precise wind speed
        data = WeatherData(place="Precise Wind", wind_speed=3.14159)
        assert data.wind_speed == 3.14159

    def test_unicode_place_names(self):
        """Test place names with unicode characters"""
        # Finnish place names with special characters
        data = WeatherData(place="Jyväskylä")
        assert data.place == "Jyväskylä"
        
        data = WeatherData(place="Säkylä")
        assert data.place == "Säkylä"
        
        data = WeatherData(place="Ähtäri")
        assert data.place == "Ähtäri"

    def test_long_place_names(self):
        """Test very long place names"""
        long_name = "Very Long Place Name That Might Cause Issues" * 10
        data = WeatherData(place=long_name)
        assert data.place == long_name

    def test_weather_description_variations(self):
        """Test various weather descriptions"""
        descriptions = [
            "clear sky",
            "few clouds",
            "scattered clouds",
            "broken clouds",
            "shower rain",
            "rain",
            "thunderstorm",
            "snow",
            "mist"
        ]
        
        for desc in descriptions:
            data = WeatherData(place="Test", weather_description=desc)
            assert data.weather_description == desc

    def test_complete_weather_data(self):
        """Test with complete realistic weather data"""
        data = WeatherData(
            place="Helsinki",
            temperature=15.2,
            feels_like=16.1,
            wind_speed=4.2,
            humidity=78,
            cloudiness=6,
            weather_description="overcast clouds"
        )
        
        # Verify all fields are set correctly
        assert data.place == "Helsinki"
        assert data.temperature == 15.2
        assert data.feels_like == 16.1
        assert data.wind_speed == 4.2
        assert data.humidity == 78
        assert data.cloudiness == 6
        assert data.weather_description == "overcast clouds"

    def test_model_serialization(self):
        """Test that the model can be serialized to dict"""
        data = WeatherData(
            place="Test",
            temperature=20.0,
            humidity=50
        )
        
        dict_data = data.model_dump()
        assert isinstance(dict_data, dict)
        assert dict_data["place"] == "Test"
        assert dict_data["temperature"] == 20.0
        assert dict_data["humidity"] == 50

    def test_model_json_serialization(self):
        """Test that the model can be serialized to JSON"""
        data = WeatherData(
            place="Test",
            temperature=20.0,
            humidity=50
        )
        
        json_data = data.model_dump_json()
        assert isinstance(json_data, str)
        assert "Test" in json_data
        assert "20.0" in json_data


@pytest.mark.skipif(not FMI_AVAILABLE, reason="FMI module dependencies not available")
class TestWAWAConstants:
    """Test WAWA weather code constants"""

    def test_wawa_constants_exist(self):
        """Test that WAWA constants are properly defined"""
        assert isinstance(WAWA, dict)
        assert len(WAWA) > 0

    def test_common_wawa_codes(self):
        """Test common WAWA weather codes"""
        # Test some known codes
        expected_codes = {
            10: "utua",
            20: "sumua", 
            21: "sadetta",
            60: "vesisadetta",
            70: "lumisadetta",
            80: "sadekuuroja"
        }
        
        for code, description in expected_codes.items():
            assert code in WAWA
            assert WAWA[code] == description

    def test_wawa_code_types(self):
        """Test that WAWA codes are integers and descriptions are strings"""
        for code, description in WAWA.items():
            assert isinstance(code, int)
            assert isinstance(description, str)
            assert len(description) > 0

    def test_wawa_code_ranges(self):
        """Test that WAWA codes are in expected ranges"""
        for code in WAWA.keys():
            # Weather codes should be positive integers
            assert code > 0
            # Most WAWA codes are in the range 10-99
            assert 10 <= code <= 99

    def test_finnish_weather_descriptions(self):
        """Test that weather descriptions are in Finnish"""
        finnish_words = ["sade", "lumi", "sumu", "utua", "kuuro"]
        descriptions = list(WAWA.values())
        
        # At least some descriptions should contain Finnish weather terms
        finnish_found = any(
            any(word in desc for word in finnish_words)
            for desc in descriptions
        )
        assert finnish_found

    def test_no_duplicate_descriptions(self):
        """Test that there are no duplicate weather descriptions"""
        descriptions = list(WAWA.values())
        unique_descriptions = set(descriptions)
        
        # Allow some duplicates as weather conditions can overlap
        # but there shouldn't be too many
        assert len(unique_descriptions) >= len(descriptions) * 0.7

    def test_precipitation_codes(self):
        """Test specific precipitation-related codes"""
        precipitation_codes = [21, 23, 24, 60, 61, 62, 63, 70, 71, 72, 73]
        
        for code in precipitation_codes:
            if code in WAWA:
                description = WAWA[code]
                # Should contain precipitation-related terms
                precipitation_terms = ["sade", "lumi", "räntä", "jyväs", "kuuro"]
                assert any(term in description for term in precipitation_terms)

    def test_fog_codes(self):
        """Test fog-related codes"""
        fog_codes = [10, 20, 30, 31, 32, 33, 34]
        
        for code in fog_codes:
            if code in WAWA:
                description = WAWA[code]
                # Should contain fog-related terms
                assert "sumu" in description or "utua" in description

    def test_intensity_descriptors(self):
        """Test that intensity descriptors are used"""
        intensity_words = ["heikko", "kohtalainen", "kova", "tiheä"]
        descriptions = list(WAWA.values())
        
        # Some descriptions should have intensity descriptors
        intensity_found = any(
            any(word in desc for word in intensity_words)
            for desc in descriptions
        )
        assert intensity_found


@pytest.mark.skipif(not FMI_AVAILABLE, reason="FMI module dependencies not available") 
class TestRealisticWeatherScenarios:
    """Test realistic weather scenarios"""

    def test_summer_weather(self):
        """Test typical summer weather data"""
        summer_data = WeatherData(
            place="Helsinki",
            temperature=25.3,
            feels_like=27.1,
            wind_speed=2.1,
            humidity=55,
            cloudiness=2,
            weather_description="few clouds"
        )
        
        assert summer_data.temperature > 20
        assert summer_data.humidity < 80
        assert summer_data.cloudiness <= 3

    def test_winter_weather(self):
        """Test typical winter weather data"""
        winter_data = WeatherData(
            place="Rovaniemi",
            temperature=-15.7,
            feels_like=-22.3,
            wind_speed=5.8,
            humidity=85,
            cloudiness=8,
            weather_description="snow"
        )
        
        assert winter_data.temperature < 0
        assert winter_data.feels_like < winter_data.temperature
        assert winter_data.humidity > 70

    def test_rainy_weather(self):
        """Test rainy weather conditions"""
        rainy_data = WeatherData(
            place="Tampere",
            temperature=12.1,
            feels_like=10.8,
            wind_speed=6.2,
            humidity=95,
            cloudiness=8,
            weather_description="heavy rain"
        )
        
        assert rainy_data.humidity >= 90
        assert rainy_data.cloudiness >= 7
        assert "rain" in rainy_data.weather_description.lower()

    def test_extreme_cold(self):
        """Test extreme cold weather"""
        extreme_cold = WeatherData(
            place="Kittilä",
            temperature=-35.2,
            feels_like=-42.1,
            wind_speed=3.5,
            humidity=70,
            cloudiness=1,
            weather_description="clear sky"
        )
        
        assert extreme_cold.temperature < -30
        assert extreme_cold.feels_like < extreme_cold.temperature

    def test_hot_summer_day(self):
        """Test very hot summer conditions"""
        hot_summer = WeatherData(
            place="Turku",
            temperature=32.8,
            feels_like=35.2,
            wind_speed=1.2,
            humidity=40,
            cloudiness=0,
            weather_description="clear sky"
        )
        
        assert hot_summer.temperature > 30
        assert hot_summer.feels_like > hot_summer.temperature
        assert hot_summer.humidity < 50

    def test_stormy_weather(self):
        """Test stormy weather conditions"""
        storm_data = WeatherData(
            place="Vaasa",
            temperature=8.5,
            feels_like=4.2,
            wind_speed=15.8,
            humidity=88,
            cloudiness=8,
            weather_description="thunderstorm"
        )
        
        assert storm_data.wind_speed > 10
        assert storm_data.feels_like < storm_data.temperature
        assert storm_data.cloudiness == 8