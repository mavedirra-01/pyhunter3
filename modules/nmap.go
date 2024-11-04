//go:build nmap
// +build nmap

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "nmapScan"
	description    = "Performs a basic Nmap scan on the target"
	author         = "Your Name"
	category       = "Network"
	installCommand = "sudo apt install nmap" // Specify the install command for dependencies
	dependencies   = []string{"nmap"}        // Specify required dependencies
	parameters     = []map[string]interface{}{
		{"name": "target", "description": "Target IP address", "required": true, "default": ""},
		{"name": "port", "description": "Port to scan", "required": false, "default": "80"},
		{"name": "options", "description": "Additional Nmap options (e.g., -sV -sC)", "required": false, "default": ""},
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
		Port    string `json:"port"`
		Options string `json:"options"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	if params.Port == "" {
		params.Port = "80"
	}

	// Build the Nmap command
	cmdArgs := []string{"-p", params.Port}

	// Add additional options if provided
	if params.Options != "" {
		cmdArgs = append(cmdArgs, params.Options)
	}

	cmdArgs = append(cmdArgs, params.Target)

	// Execute the Nmap command
	cmd := exec.Command("nmap", cmdArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute nmap: %s\"}\n", err)
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
