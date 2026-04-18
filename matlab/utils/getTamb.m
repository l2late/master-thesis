function [datetime, ambient_temperature, total_solar_radiation] = getTamb()
%GETTAMB Reads ambient temperature data from Rotterdam.
%   [datetime, temperature] = GETTAMB(	) reads the CSV file containing
%   outdoor air drybulb temperature for Rotterdam.
%
%   Output:
%       datetime    - Array of datetime objects
%       temperature - Array of temperature values (numeric)
%
%   Example:
%       [dt, T] = getTamb(2022);

    % Construct the file path
    base_path = "/home/l2late/stack/Master/Thesis/master-thesis-code/alpha_building_model/data/processed/";
    csv_filepath = fullfile(base_path, "knmi_data_2021_10min.csv");

    % Read the CSV file
    opts = detectImportOptions(csv_filepath);
    T = readtable(csv_filepath, opts);

    % Try to find suitable column names for datetime and temperature
    dt_col = 1;
    amb_temp_col = find(contains(lower(T.Properties.VariableNames), "temp"), 1);
    total_solar_radiation_col = find(contains(lower(T.Properties.VariableNames), "radiation"), 1);

    if isempty(dt_col) || isempty(amb_temp_col)
        error("Could not find suitable datetime or temperature columns in the CSV file.");
    end

    % Extract data
    datetime = T{:, dt_col};
    ambient_temperature = T{:, amb_temp_col};
    total_solar_radiation = T{:,total_solar_radiation_col};

    % Convert datetime if necessary
    if ~isdatetime(datetime)
        try
            datetime = datetime(datetime, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
        catch
            warning("Could not parse datetime format automatically.");
        end
    end
    
    % FIX: Shift Solar Radiation values backward by one index.
    % Explanation:
    % KNMI timestamp at HH:00 for 'Q' means radiation sum over interval [HH-1:00, HH:00].
    % We want the value at index 'i' to represent the radiation STARTING at datetime(i).
    % So the radiation sum ending at 12:00 (index i) should be assigned to 11:00 (index i-1).
    % We discard the first radiation measurement (which belongs to the hour before the dataset starts)
    % and pad the end to maintain array length.

    total_solar_radiation = [total_solar_radiation(2:end); total_solar_radiation(end)];

    % Verify lengths match (sanity check)
    if length(datetime) ~= length(total_solar_radiation)
        error('Array length mismatch after shifting solar radiation');
    end
end


