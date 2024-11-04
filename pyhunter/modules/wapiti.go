//go:build wapiti
// +build wapiti

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "wapitiScan"
	description    = "Performs a vulnerability scan using Wapiti with configurable options"
	author         = "Your Name"
	category       = "Web"
	installCommand = "sudo apt install wapiti"
	dependencies   = []string{"wapiti"}
	parameters     = []map[string]interface{}{
		{"name": "url", "description": "Target URL to scan", "required": true, "default": ""},
		{"name": "scope", "description": "Scope for the scan (e.g., folder, domain, url)", "required": false, "default": "folder"},
		{"name": "proxy", "description": "Proxy URL (e.g., http://localhost:8080)", "required": false, "default": ""},
		{"name": "timeout", "description": "Request timeout in seconds", "required": false, "default": "30"},
		{"name": "modules", "description": "Modules to enable (e.g., sql, xss, all)", "required": false, "default": "all"},
		{"name": "verify_ssl", "description": "Verify SSL certificates (true/false)", "required": false, "default": "true"},
		{"name": "level", "description": "Scan depth level", "required": false, "default": "1"},
		{"name": "options", "description": "Additional Wapiti options", "required": false, "default": ""},
	}
)

func main() {
	metadata := flag.Bool("metadata", false, "Output metadata as JSON")
	var paramsJSON string
	flag.StringVar(&paramsJSON, "params", "", "JSON string containing module parameters")
	flag.Parse()

	if *metadata {
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

	var params struct {
		URL       string `json:"url"`
		Scope     string `json:"scope"`
		Proxy     string `json:"proxy"`
		Timeout   string `json:"timeout"`
		Modules   string `json:"modules"`
		VerifySSL string `json:"verify_ssl"`
		Level     string `json:"level"`
		Options   string `json:"options"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Build the Wapiti command
	cmdArgs := []string{"-u", params.URL}

	// Add optional parameters based on user input
	if params.Scope != "" {
		cmdArgs = append(cmdArgs, "--scope", params.Scope)
	}
	if params.Proxy != "" {
		cmdArgs = append(cmdArgs, "--proxy", params.Proxy)
	}
	if params.Timeout != "" {
		cmdArgs = append(cmdArgs, "--timeout", params.Timeout)
	}
	if params.Modules != "" {
		cmdArgs = append(cmdArgs, "--module", params.Modules)
	}
	if params.VerifySSL == "false" {
		cmdArgs = append(cmdArgs, "--no-verify")
	}
	if params.Level != "" {
		cmdArgs = append(cmdArgs, "--level", params.Level)
	}

	// Include additional options provided by the user
	if params.Options != "" {
		cmdArgs = append(cmdArgs, params.Options)
	}

	// Execute the Wapiti command
	cmd := exec.Command("wapiti", cmdArgs...)
	println(cmd.String())
	output, err := cmd.CombinedOutput()
	println(string(output))
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute wapiti: %s\"}\n", err)
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
