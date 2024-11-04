//go:build sqlmap
// +build sqlmap

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "sqlmapScan"
	description    = "Performs an SQL injection scan using SQLMap with configurable options"
	author         = "Your Name"
	category       = "Database"
	installCommand = "sudo apt install sqlmap" // Specify the install command for dependencies
	dependencies   = []string{"sqlmap"}        // Specify required dependencies
	parameters     = []map[string]interface{}{
		{"name": "url", "description": "Target URL for SQL injection testing", "required": true, "default": ""},
		{"name": "data", "description": "POST data to inject", "required": false, "default": ""},
		{"name": "cookie", "description": "Cookie to use for the request", "required": false, "default": ""},
		{"name": "auth_type", "description": "Authentication type (e.g., basic, digest)", "required": false, "default": ""},
		{"name": "auth_credentials", "description": "Credentials for authentication (e.g., 'user:pass')", "required": false, "default": ""},
		{"name": "dbms", "description": "Specify the DBMS (e.g., MySQL, PostgreSQL)", "required": false, "default": ""},
		{"name": "level", "description": "Testing level (1-5)", "required": false, "default": "1"},
		{"name": "risk", "description": "Risk level (1-3)", "required": false, "default": "1"},
		{"name": "proxy", "description": "Proxy URL to use (e.g., http://localhost:8080)", "required": false, "default": ""},
		{"name": "timeout", "description": "Request timeout in seconds", "required": false, "default": "30"},
		{"name": "threads", "description": "Number of concurrent threads", "required": false, "default": "1"},
		{"name": "options", "description": "Additional SQLMap options", "required": false, "default": ""},
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
		URL             string `json:"url"`
		Data            string `json:"data"`
		Cookie          string `json:"cookie"`
		AuthType        string `json:"auth_type"`
		AuthCredentials string `json:"auth_credentials"`
		DBMS            string `json:"dbms"`
		Level           string `json:"level"`
		Risk            string `json:"risk"`
		Proxy           string `json:"proxy"`
		Timeout         string `json:"timeout"`
		Threads         string `json:"threads"`
		Options         string `json:"options"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Build the SQLMap command
	cmdArgs := []string{"-u", params.URL}

	// Add optional parameters based on user input
	if params.Data != "" {
		cmdArgs = append(cmdArgs, "--data", params.Data)
	}
	if params.Cookie != "" {
		cmdArgs = append(cmdArgs, "--cookie", params.Cookie)
	}
	if params.AuthType != "" && params.AuthCredentials != "" {
		cmdArgs = append(cmdArgs, "--auth-type", params.AuthType, "--auth-cred", params.AuthCredentials)
	}
	if params.DBMS != "" {
		cmdArgs = append(cmdArgs, "--dbms", params.DBMS)
	}
	if params.Level != "" {
		cmdArgs = append(cmdArgs, "--level", params.Level)
	}
	if params.Risk != "" {
		cmdArgs = append(cmdArgs, "--risk", params.Risk)
	}
	if params.Proxy != "" {
		cmdArgs = append(cmdArgs, "--proxy", params.Proxy)
	}
	if params.Timeout != "" {
		cmdArgs = append(cmdArgs, "--timeout", params.Timeout)
	}
	if params.Threads != "" {
		cmdArgs = append(cmdArgs, "--threads", params.Threads)
	}

	// Include additional options provided by the user
	if params.Options != "" {
		cmdArgs = append(cmdArgs, params.Options)
	}

	// Execute the SQLMap command
	cmd := exec.Command("sqlmap", cmdArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute sqlmap: %s\"}\n", err)
		os.Exit(1)
	}

	// Prepare the output in JSON format
	result := struct {
		Output string `json:"output"`
	}{
		Output: string(output),
	}
	resultJSON, _ := json.Marshal(result)
	fmt.Println(string(resultJSON))
}
