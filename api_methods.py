class APIFramework:
    def traverse(self, json_obj, key=None, value=None, target_object=None, expected_length=None):
        if isinstance(json_obj, dict):
            # Key-value pair validation
            if key is not None and value is not None:
                if key in json_obj and json_obj[key] == value:
                    return True
            # Array length validation
            if key is not None and expected_length is not None:
                if key in json_obj and isinstance(json_obj[key], list):
                    actual_array_length = len(json_obj[key])
                    if actual_array_length == expected_length:
                        return True
                    else:
                        return False
            # Object presence validation
            if target_object is not None:
                if json_obj == target_object:
                    return True
            # Recursively search each value in the dictionary
            for v in json_obj.values():
                result = self.traverse(v, key, value, target_object, expected_length)
                if isinstance(result, tuple):
                    return result
                elif result:
                    return True
        elif isinstance(json_obj, list):
            # Recursively search each item in the list
            for item in json_obj:
                result = self.traverse(item, key, value, target_object, expected_length)
                if isinstance(result, tuple):
                    return result
                elif result:
                    return True
        return False

    def validate_key_value(self, json_data, key, value):
        return self.traverse(json_data, key=key, value=value)

    def is_object_present(self, json_data, key, target_object):
        return self.traverse(json_data, key=key, target_object=target_object)

    def validate_array_length(self, json_data, key, expected_length):
        return self.traverse(json_data, key=key, expected_length=expected_length)

    def check_values_in_array(self, json_data, key, values, operation="equals_to"):
        if isinstance(json_data, dict) and key in json_data and isinstance(json_data[key], list):
            array_values = json_data[key]
            if operation == "equals_to":
                if set(values) == set(array_values):
                    return True
            elif operation == "contains":
                if set(values).issubset(set(array_values)):
                    return True
        return False


