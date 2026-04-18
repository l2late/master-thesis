classdef Progressdisp < handle
    % PROGRESSDISP: A class to display the progress of a for-loop in the MATLAB command prompt.
    %
    % This class provides a visual representation of loop progress using either:
    %   1. A progress bar (default mode): A graphical bar that fills as the loop progresses.
    %   2. A text-based counter: A message displaying the current iteration out of the total.
    %
    % In addition, Progressdisp now supports displaying custom messages above the progress
    % display via two new methods:
    %   - Disp(input_string): Displays a custom message above the progress display.
    %   - Disp_over(input_string): Overwrites any existing top text with a new message.
    %
    % USAGE:
    %   obj = Progressdisp(nIter, options)
    %
    %   Input arguments:
    %       - nIter: Total number of iterations (numeric).
    %       - options (name-value pairs):
    %           - 'barWidth' (optional): Width of the progress bar (default is 40 characters).
    %           - 'BarOrStr' (optional): Choose the display type:
    %                                   "bar" for a progress bar (default) or "str" for a text counter.
    %
    %   EXAMPLE:
    %       Displayer = Progressdisp(300, barWidth=40, BarOrStr="bar");
    %       for i = 1:300
    %           Displayer.Display_progress(i);
    %           % Optionally display custom messages:
    %           % Displayer.Disp("Processing data...");
    %           % or
    %           % Displayer.Disp_over("New configuration loaded.");
    %           pause(0.01); % Simulate work
    %       end
    %
    % METHODS:
    %   - Display_progress(current_iter): Updates and displays the current progress.
    %   - Disp(input_string): Displays a custom text message above the progress display.
    %   - Disp_over(input_string): Overwrites any existing custom top text with a new message.
    %   The progress display is continuously updated in place, ensuring that the command prompt
    %   remains uncluttered.
    %
    % Author: Hiroto Imamura
    
    properties
        nIter {mustBeNumeric}              % Total number of iterations
        Current_iter {mustBeNumeric}       % Current iteration (reserved for future use)
        barWidth {mustBeNumeric}           % Width of the progress bar
        BarOrStr                        	% Mode: "bar" for a progress bar, "str" for a text counter
        progressBar                     	% Stores the current progress bar string (if in "bar" mode)
        charString                      	% Stores the current text string (if in "str" mode)
        Displayed                       	% Stores the last displayed progress message (for erasing previous output)
        Displayed_length                	% The number of characters in the last displayed progress message
        nIter_numDigits                 	% Number of digits in nIter (used for formatting)
        input_string_length             	% Length of the input text message displayed above the progress display
    end
    
    methods
        % Constructor: Initializes the progress display
        function obj = Progressdisp(nIter, options)
            arguments
                nIter {mustBeNumeric}                    % Total iterations (numeric)
                options.barWidth {mustBeNumeric} = 40      % Default bar width is 40 characters
                options.BarOrStr {mustBeMember(options.BarOrStr, ["bar", "str"])} = "bar"
                % BarOrStr can be "bar" (default) or "str"
            end
            
            % Store the input parameters
            obj.nIter = nIter;
            obj.barWidth = options.barWidth;
            obj.BarOrStr = options.BarOrStr;
            obj.input_string_length = 0;
            
            % Determine the number of digits in nIter (used for output formatting)
            obj.nIter_numDigits = length(num2str(floor(abs(obj.nIter))));
            current_iter_numDigits = length(num2str(0));
            
            % Initialize display based on the selected mode ("bar" or "str")
            switch obj.BarOrStr
                case "bar"
                    % Create an initial progress bar string.
                    % The progress bar shows 0% completion initially.
                    progressBar = ['\n', sprintf('%3.0f', 0), '%% [', repmat('-', 1, obj.barWidth), '] ', sprintf('%d/%d', 0, obj.nIter)];
                    fprintf(progressBar);  % Print the initial progress bar
                    obj.progressBar = progressBar;
                    obj.Displayed = progressBar;
                    % Calculate and store the length of the displayed string for proper erasing later.
                    obj.Displayed_length = obj.barWidth + 5 + 3 + current_iter_numDigits + obj.nIter_numDigits + 1;
                    
                case "str"
                    % Create an initial text message for progress display.
                    charString = ['\nLoop <strong>', num2str(0), '</strong> out of <strong>', num2str(nIter), '</strong>'];
                    fprintf(charString);  % Print the initial text-based progress message
                    obj.charString = charString;
                    obj.Displayed = charString;
                    % Set the displayed length (used for erasing the previous message).
                    obj.Displayed_length = 13 + current_iter_numDigits + obj.nIter_numDigits;
            end
        end
        
        % Method: Display_progress
        % Updates and displays the current progress based on the current iteration.
        function Display_progress(obj, current_iter)
            % Determine the number of digits in the current iteration (for formatting)
            current_iter_numDigits = length(num2str(floor(abs(current_iter))));
            
            % Update the display based on the selected mode
            switch obj.BarOrStr
                case "bar"
                    % Calculate the percentage of completion
                    percentDone = current_iter / obj.nIter * 100;
                    
                    % Determine the number of filled characters (hashes) and unfilled (dashes)
                    numHashes = round(current_iter / obj.nIter * obj.barWidth);
                    numDashes = obj.barWidth - numHashes;
                    
                    % Create the updated progress bar string
                    newProgressBar = [sprintf('%3.0f', percentDone), '%% [', ...
                        repmat('#', 1, numHashes), repmat('-', 1, numDashes), '] ', ...
                        sprintf('%d/%d', current_iter, obj.nIter)];
                    
                    % Erase the previous progress bar by printing backspace characters
                    fprintf(repmat('\b', 1, obj.Displayed_length));
                    fprintf(newProgressBar);  % Print the updated progress bar
                    
                    % Update the stored displayed length and progress bar string
                    obj.Displayed_length = obj.barWidth + 5 + 3 + current_iter_numDigits + obj.nIter_numDigits + 1;
                    obj.Displayed = newProgressBar;
                    obj.progressBar = newProgressBar;
                    
                case "str"
                    % Create the updated text-based progress string
                    charString = ['Loop <strong>', num2str(current_iter), '</strong> out of <strong>', num2str(obj.nIter), '</strong>'];
                    
                    % Erase the previous string by printing backspaces
                    fprintf(repmat('\b', 1, obj.Displayed_length));
                    fprintf(charString);  % Print the updated text message
                    
                    % Update the stored displayed length and text string
                    obj.Displayed_length = 13 + current_iter_numDigits + obj.nIter_numDigits;
                    obj.charString = charString;
                    obj.Displayed = charString;
            end
        end
        
        % Method: Disp
        % Displays a custom text message above the progress display without overwriting existing top text.
        function Disp(obj, input_string)
            arguments
                obj
                input_string {mustBeText}
            end
            % Erase the current progress display (without affecting the top text area)
            fprintf(repmat('\b', 1, obj.Displayed_length));
            % Display the custom input string
            disp(input_string);
            % Update the length of the input string (including a line break)
            obj.input_string_length = strlength(input_string) + 1;
            % Reprint the current progress display
            fprintf(obj.Displayed);
        end
        
        % Method: Disp_over
        % Overwrites any existing custom top text with a new message above the progress display.
        function Disp_over(obj, input_string)
            arguments
                obj
                input_string {mustBeText}
            end
            % Erase the current progress display
            fprintf(repmat('\b', 1, obj.Displayed_length));
            % Also erase any previously displayed custom top text
            fprintf(repmat('\b', 1, obj.input_string_length));
            % Display the new custom input string
            disp(input_string);
            % Update the length of the input string (including a line break)
            obj.input_string_length = strlength(input_string) + 1;
            % Reprint the current progress display
            fprintf(obj.Displayed);
        end
    end
end
