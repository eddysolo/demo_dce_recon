#/bin/bin -l
# Function to extract case number and suffix

if [ -z "$1" ]; then
    echo "Find raw .h5 files in the current directory: $(pwd)"
    DIR=$(pwd)
else
    echo "Find raw .h5 files in: $1"
    DIR="$1"
fi

FILES=$(find "${DIR}" -maxdepth 1 -type f -name "*CCCTrio*.h5" -exec basename {} \;)

#printf "old list:\n"
#printf "%s\n" "${FILES[@]}"

# Create a copy of the original case list
unsorted_cases=("${FILES[@]}")


# Sort the list of cases
sorted_cases=($(printf "%s\n" "${unsorted_cases[@]}" | sort -t '#' -k2n))

# Display sorted list of cases
#printf "sorted list:\n"
#printf "%s\n" "${sorted_cases[@]}"

# Create a new array variable to store the converted list
new_list=()

# Create conversion table and save to Excel
printf "Case\tPatient Name\n" > conversion_table.tsv
for case in "${sorted_cases[@]}"; do
    # Extract F number
    if [[ "$case" =~ \#F([0-9]+)\.h5 ]]; then
        f_number="${BASH_REMATCH[1]}"
        # Check if F number exists in the patient_serial_numbers array
        if [[ ! "${patient_serial_numbers[$f_number]}" ]]; then
            # Increment serial_counter and assign to patient_serial_numbers
            ((serial_counter++))
            patient_serial_numbers[$f_number]=$(printf "%03d" "$serial_counter")
        fi
        # Retrieve patient serial number
        patient_serial_number="${patient_serial_numbers[$f_number]}"
        # Extract segment number
        if [[ "$case" =~ seg([0-9]+) ]]; then
            segment_number="${BASH_REMATCH[1]}"
            # Format patient name
            #patient_name="fastMRI_breast_${patient_serial_number}_${f_number}_${segment_number}.h5"
            patient_name="fastMRI_breast_${patient_serial_number}_${segment_number}"
            # Print patient name
            printf "%s\t%s\n" "$case" "$patient_name" >> conversion_table.tsv
            # Append patient name to new list
            new_list+=("$patient_name")
        else
            printf "Segment number not found in case: %s\n" "$case" >&2
        fi
    else
        printf "F number not found in case: %s\n" "$case" >&2
    fi
done

# Print the new list
#printf "coded list:\n"
#printf "%s\n" "${new_list[@]}"

#over write the original case list
FILES=("${sorted_cases[@]}")


if [ -z "${FILES}" ]; then
    echo "no raw .h5 file found. exit."
    exit
fi

if [ -z "$2" ]; then
    echo "> SPOKES set as default: 72"
    SPOKES=72
else
    NUM='^[0-9]+$'

    if [[ $2 =~ $NUM ]]; then
        SPOKES="$2"
    else
        echo "> Input $2 is not a number. SPOKES set as default: 72"
        SPOKES=72
    fi
fi

#echo "> reconstruct files: ${FILES[@]}"

counter=0
for F in ${FILES[@]};
do

    new_F="${new_list[counter]}"
    echo "> ${F} ----> ${new_F}"

    # reconstruct slice by slice
    python dce_recon_comb.py --dir ${DIR} --data ${F} --codedName ${new_F} --spokes_per_frame ${SPOKES} --slice_idx 0 --slice_inc 192

    # convert the .h5 file to dicom
    FN=${new_F}
    #echo "> FN: ${FN}"
    python h5_to_dcm.py --h5py ${FN} --spokes_per_frame ${SPOKES}

    ((counter++))

done
