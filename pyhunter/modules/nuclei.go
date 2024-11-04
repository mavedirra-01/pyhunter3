//go:build nuclei
// +build nuclei

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "nucleiScan"
	description    = "Performs vulnerability scanning using Nuclei"
	author         = "Your Name"
	category       = "Security"
	installCommand = "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest" // Specify the install command for dependencies
	dependencies   = []string{"nuclei"}                                                      // Specify required dependencies
	parameters     = []map[string]interface{}{
		{"name": "target", "description": "Target URL or IP address", "required": true, "default": ""},
		{"name": "templates", "description": "Comma-separated list of templates to use", "required": false, "default": "all"},
		{"name": "severity", "description": "Specify severity level (low, medium, high, critical)", "required": false, "default": ""},
		{"name": "output", "description": "File to save output results", "required": false, "default": ""},
	}
)

func main() {
	metadata := flag.Bool("metadata", false, "Output metadata as JSON")
	var paramsJSON string
	flag.StringVar(&paramsJSON, "params", "", "JSON string containing module parameters")
	flag.Parse()

	if *metadata {
		// Output the metadata as JSON and exit
		meta := map[string]interface{}{
			"name":            name,
			"description":     description,
			"author":          author,
			"category":        category,
			"parameters":      parameters,
			"dependencies":    dependencies,
			"install_command": installCommand,
		}
		metaJSON, _ := json.Marshal(meta)
		fmt.Println(string(metaJSON))
		return
	}

	// Normal operation mode for executing the module logic
	var params struct {
		Target    string `json:"target"`
		Templates string `json:"templates"`
		Severity  string `json:"severity"`
		Output    string `json:"output"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Build the command based on provided parameters
	cmd := exec.Command("nuclei", "-u", params.Target)
	if params.Templates != "" {
		cmd.Args = append(cmd.Args, "-t", params.Templates)
	}
	if params.Severity != "" {
		cmd.Args = append(cmd.Args, "-severity", params.Severity)
	}
	if params.Output != "" {
		cmd.Args = append(cmd.Args, "-o", params.Output)
	}

	println(cmd.String())

	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute nuclei: %s\"}\n", err)
		os.Exit(1)
	}

	result := struct {
		Output string `json:"output"`
	}{
		Output: string(output),
	}
	resultJSON, _ := json.Marshal(result)
	fmt.Println(string(resultJSON))
}
