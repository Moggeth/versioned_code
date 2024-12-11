import os
import subprocess
from openai import OpenAI
from colorama import Fore, Style

# Initialize OpenAI client
client = OpenAI()

# Directory to save generated scripts
output_dir = "generated_scripts"
os.makedirs(output_dir, exist_ok=True)

# Initial prompt for the first code generation
initial_prompt = "Write a Python script that uses the Google Scholar API to search for 'can insects feel pain' and returns the article titles of the first 5 results. Return only Python code, no explanations or comments."

# Function to save the generated script to a file
def save_script(script_content, version):
    filename = os.path.join(output_dir, f"script_v{version}.py")
    with open(filename, "w") as file:
        file.write(script_content)
    return filename

# Function to execute a Python script and capture its output
def run_script(filename):
    try:
        result = subprocess.run(
            ["python", filename],
            text=True,
            capture_output=True
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

# Function to determine if further iterations are needed
def are_we_done(script_content, stdout, stderr):
    prompt = (
        f"The following Python script was generated and executed. Here is the code:\n\n"
        f"{script_content}\n\n"
        f"And here is its output:\n\n"
        f"{stdout}\n"
        f"Errors (if any):\n\n{stderr}\n\n"
        "Is this script complete, or does it require further iterations? Respond with 'True' if complete and 'False' if further improvement is needed."
    )

    print(Fore.BLUE + "\n[GPT Request]:" + Style.RESET_ALL)
    print(prompt)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    completion_text = response.choices[0].message.content.strip().lower()
    return completion_text == "true"

# Function to detect and list required human inputs
def detect_human_inputs(script_content, stdout, stderr):
    prompt = (
        f"The following Python script was generated and executed. Here is the code:\n\n"
        f"{script_content}\n\n"
        f"And here is its output:\n\n"
        f"{stdout}\n"
        f"Errors (if any):\n\n{stderr}\n\n"
        "Does this script require any additional human input, such as API keys or specific configuration settings, to function? If so, list them explicitly."
    )

    print(Fore.MAGENTA + "\n[Checking for Required Human Inputs]:" + Style.RESET_ALL)
    print(prompt)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    human_input_needed = response.choices[0].message.content.strip()
    return human_input_needed

# Main loop for iterative script generation and execution
def main():
    version = 1
    current_prompt = initial_prompt

    while version <= 5:  # Limit iterations to prevent infinite loops
        print(Fore.GREEN + f"\n[Step]: Generating script version {version}..." + Style.RESET_ALL)

        # Request new code from GPT-4o
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": current_prompt}],
            stream=True,
        )

        print(Fore.YELLOW + "[GPT Thinking]:" + Style.RESET_ALL, end="")
        script_content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(Fore.YELLOW + "." + Style.RESET_ALL, end="", flush=True)
                script_content += chunk.choices[0].delta.content
        print()  # End stream output

        # Strip any non-code content from the generated script
        script_content = "\n".join(
            line for line in script_content.splitlines()
            if not line.strip().startswith("#") and not line.strip().startswith("Certainly") and "```" not in line
        )

        # Save the new script
        filename = save_script(script_content, version)

        # Run the script and capture output
        stdout, stderr = run_script(filename)

        # Print results
        print(Fore.CYAN + f"\n[Output from script_v{version}.py]:" + Style.RESET_ALL)
        print(stdout)
        if stderr:
            print(Fore.RED + f"[Errors]:\n{stderr}" + Style.RESET_ALL)

        # Check if additional human input is required
        human_inputs = detect_human_inputs(script_content, stdout, stderr)
        if human_inputs and "none" not in human_inputs.lower():
            print(Fore.MAGENTA + "\n[Human Input Required]:" + Style.RESET_ALL)
            print(human_inputs)
            print(Fore.MAGENTA + "\n[Pausing for human input. Please provide the necessary information and restart the script if needed.]" + Style.RESET_ALL)
            break

        # Check if the script is complete
        if are_we_done(script_content, stdout, stderr):
            print(Fore.GREEN + "\n[Success]: The script is complete. No further iterations are needed." + Style.RESET_ALL)
            break

        # Generate the next prompt
        current_prompt = (
            f"The following Python script was generated and executed. Here is the code:\n\n"
            f"{script_content}\n\n"
            f"And here is its output:\n\n"
            f"{stdout}\n"
            f"Errors (if any):\n\n{stderr}\n\n"
            "Now improve the script by addressing any errors and enhancing its functionality, such as adding a feature to handle custom ranges or more comprehensive error handling."
        )

        version += 1

if __name__ == "__main__":
    main()
