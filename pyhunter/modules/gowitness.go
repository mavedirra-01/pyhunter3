//go:build gowitness
// +build gowitness

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "gowitnessScan"
	description    = "Takes screenshots of websites using Gowitness"
	author         = "Your Name"
	category       = "Web"
	installCommand = "sudo apt install gowitness" // Specify the install command for dependencies
	dependencies   = []string{"gowitness"}        // Specify required dependencies
	parameters     = []map[string]interface{}{
		{"name": "target", "description": "Target URL or file with URLs", "required": true, "default": ""},
		{"name": "options", "description": "Additional Gowitness options (e.g., -f)", "required": false, "default": ""},
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
		Target  string `json:"target"`
		Options string `json:"options"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Build the Gowitness command
	cmdArgs := []string{"scan", "single", "--url", params.Target}

	// Add additional options if provided
	if params.Options != "" {
		cmdArgs = append(cmdArgs, params.Options)
	}

	// Execute the Gowitness command
	cmd := exec.Command("gowitness", cmdArgs...)
	// println(cmd.String())
	output, err := cmd.CombinedOutput()
	// println(string(output))
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute gowitness: %s\"}\n", err)
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
